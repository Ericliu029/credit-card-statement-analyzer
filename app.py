from __future__ import annotations

import importlib
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from categorization import add_custom_rule, list_custom_rules, remove_custom_rule
from services import database_service
from services.local_llm_service import DEFAULT_MODEL, OllamaClient, classify_merchants
from services.pdf_service import extract_text_from_pdf
from services.transaction_service import parse_statement_text, sample_transactions


if not hasattr(database_service.Database, "has_users"):
    database_service = importlib.reload(database_service)

Database = database_service.Database
default_database_path = database_service.default_database_path
statement_fingerprint = database_service.statement_fingerprint


CATEGORIES = [
    "Dining",
    "Groceries",
    "Transportation",
    "Shopping",
    "Travel",
    "Utilities",
    "Entertainment",
    "Health",
    "Fees",
    "Payments & Credits",
    "Other",
    "Uncategorized",
]

CATEGORY_EMOJIS = {
    "Dining": "🍽️",
    "Groceries": "🛒",
    "Transportation": "🚇",
    "Shopping": "🛍️",
    "Travel": "✈️",
    "Utilities": "💡",
    "Entertainment": "🎬",
    "Health": "🩺",
    "Fees": "🧾",
    "Payments & Credits": "💳",
    "Other": "📦",
    "Uncategorized": "❓",
}

INTERNAL_COLUMNS = [
    "_statement_hash",
    "_statement_filename",
    "_issuer",
    "_is_saved",
]

APP_ICON_PATH = Path(__file__).resolve().parent / "assets" / "app-icon.png"


def get_database(path: str) -> Database:
    database = Database(path)
    database.initialize()
    return database


def render_category_grid(category_data: pd.DataFrame, total: float) -> None:
    items = []
    for row in category_data.itertuples(index=False):
        category = str(row.category)
        share = row.amount / total if total else 0
        emoji = CATEGORY_EMOJIS.get(category, "📌")
        items.append(
            f'<div class="category-tile">'
            f'<div class="category-emoji">{emoji}</div>'
            f'<div class="category-name">{escape(category)}</div>'
            f'<div class="category-amount">${row.amount:,.2f}</div>'
            f'<div class="category-meta">{share:.1%} · {row.transactions} '
            f"transaction{'s' if row.transactions != 1 else ''}</div>"
            f"</div>"
        )

    st.markdown(
        """
        <style>
        .category-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            margin: 4px 0 20px;
        }
        .category-tile {
            min-width: 0;
            min-height: 132px;
            padding: 16px;
            border: 1px solid rgba(49, 51, 63, 0.16);
            border-radius: 6px;
            background: rgba(248, 249, 251, 0.72);
        }
        .category-emoji {
            min-height: 36px;
            font-size: 26px;
            line-height: 36px;
        }
        .category-name {
            overflow-wrap: anywhere;
            color: rgb(49, 51, 63);
            font-size: 15px;
            font-weight: 600;
        }
        .category-amount {
            margin-top: 8px;
            color: rgb(49, 51, 63);
            font-size: 17px;
            font-weight: 600;
        }
        .category-meta {
            margin-top: 2px;
            color: rgba(49, 51, 63, 0.68);
            font-size: 13px;
        }
        @media (max-width: 700px) {
            .category-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .category-tile { min-height: 126px; padding: 14px; }
        }
        </style>
        """
        + '<div class="category-grid">'
        + "".join(items)
        + "</div>",
        unsafe_allow_html=True,
    )


def prepare_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    prepared = dataframe.copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    prepared["amount"] = pd.to_numeric(prepared["amount"], errors="coerce").fillna(0)
    prepared["category"] = prepared["category"].fillna("Uncategorized")
    prepared["month"] = prepared["date"].dt.to_period("M").astype(str)
    return prepared


def render_month_filter(dataframe: pd.DataFrame, key: str) -> pd.DataFrame:
    available_months = sorted(dataframe["month"].dropna().unique(), reverse=True)
    with st.sidebar:
        selected_months = st.multiselect(
            "Months",
            available_months,
            default=available_months,
            key=key,
        )
    if not selected_months:
        return dataframe
    return dataframe[dataframe["month"].isin(selected_months)]


def render_dashboard(dataframe: pd.DataFrame) -> None:
    spending_dataframe = dataframe[dataframe["amount"] > 0].copy()
    total_spending = spending_dataframe["amount"].sum()
    transaction_count = len(spending_dataframe)
    average_transaction = total_spending / transaction_count if transaction_count else 0
    categorized_count = int((spending_dataframe["category"] != "Uncategorized").sum())
    categorized_rate = categorized_count / transaction_count if transaction_count else 0

    st.subheader("Summary")
    if transaction_count:
        category_totals = spending_dataframe.groupby("category")["amount"].sum().sort_values(ascending=False)
        top_category = category_totals.index[0]
        top_category_amount = category_totals.iloc[0]
        top_category_share = top_category_amount / total_spending if total_spending else 0
        highest_expense = spending_dataframe.loc[spending_dataframe["amount"].idxmax()]
        uncategorized_count = transaction_count - categorized_count
        month_count = spending_dataframe["month"].nunique()

        summary_parts = [
            f"Across **{month_count} month(s)**, spending totals **${total_spending:,.2f}** "
            f"across **{transaction_count} transactions**.",
            f"The largest category is **{top_category}** at **${top_category_amount:,.2f}** "
            f"({top_category_share:.0%} of spending).",
            f"The highest single expense is **{highest_expense['merchant']}** at "
            f"**${highest_expense['amount']:,.2f}**.",
        ]

        monthly_totals = spending_dataframe.groupby("month")["amount"].sum().sort_index()
        if len(monthly_totals) >= 2 and monthly_totals.iloc[-2]:
            change = (monthly_totals.iloc[-1] - monthly_totals.iloc[-2]) / monthly_totals.iloc[-2]
            direction = "increased" if change >= 0 else "decreased"
            summary_parts.append(
                f"In **{monthly_totals.index[-1]}**, spending {direction} "
                f"**{abs(change):.1%}** from the previous month."
            )

        if uncategorized_count:
            summary_parts.append(f"**{uncategorized_count} transactions** still need a category review.")
        st.info(" ".join(summary_parts))
    else:
        st.info("No spending transactions are available for the selected filters.")

    with st.container(horizontal=True):
        st.metric("Total spending", f"${total_spending:,.2f}", border=True)
        st.metric("Transactions", f"{transaction_count}", border=True)
        st.metric("Average transaction", f"${average_transaction:,.2f}", border=True)
        st.metric("Categorized", f"{categorized_rate:.0%}", border=True)

    if spending_dataframe.empty:
        return

    st.subheader("Monthly Overview")
    monthly = (
        spending_dataframe.groupby("month", as_index=False)
        .agg(
            total_spending=("amount", "sum"),
            transactions=("amount", "size"),
            average_transaction=("amount", "mean"),
        )
        .sort_values("month")
    )
    monthly["average_transaction"] = monthly["average_transaction"].round(2)
    st.plotly_chart(
        px.bar(
            monthly,
            x="month",
            y="total_spending",
            text_auto="$.2s",
            labels={"month": "Month", "total_spending": "Spending"},
        ),
        width="stretch",
    )
    st.dataframe(
        monthly,
        width="stretch",
        hide_index=True,
        column_config={
            "month": st.column_config.TextColumn("Month"),
            "total_spending": st.column_config.NumberColumn("Total spending", format="$%.2f"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "average_transaction": st.column_config.NumberColumn("Average", format="$%.2f"),
        },
    )

    st.subheader("Daily Spending")
    daily = spending_dataframe.groupby(spending_dataframe["date"].dt.date, as_index=False)["amount"].sum()
    st.plotly_chart(px.bar(daily, x="date", y="amount"), width="stretch")

    st.subheader("Spending by Category")
    by_category = (
        spending_dataframe.groupby("category", as_index=False)
        .agg(amount=("amount", "sum"), transactions=("amount", "size"))
        .sort_values("amount", ascending=False)
    )
    category_chart = px.pie(
        by_category,
        names="category",
        values="amount",
        hole=0.48,
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    category_chart.update_traces(
        textposition="outside",
        texttemplate="%{label} %{percent:.1%}",
        hovertemplate="%{label}<br>$%{value:,.2f}<br>%{percent:.1%}<extra></extra>",
        sort=False,
    )
    category_chart.update_layout(
        height=520,
        showlegend=False,
        margin=dict(l=120, r=120, t=24, b=24),
        uniformtext_minsize=12,
        uniformtext_mode="show",
    )
    st.plotly_chart(category_chart, width="stretch")
    render_category_grid(by_category, total_spending)

    st.subheader("Top Expenses")
    top_expenses = spending_dataframe.sort_values("amount", ascending=False).head(10)
    st.dataframe(
        top_expenses[["date", "merchant", "category", "amount"]],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Spending by Card")
    by_card = spending_dataframe.groupby("card", as_index=False)["amount"].sum()
    st.plotly_chart(px.bar(by_card, x="card", y="amount"), width="stretch")


def dataframe_from_parsed_transactions(
    transactions: list,
    *,
    file_hash: str,
    filename: str,
    issuer: str,
    is_saved: bool,
) -> pd.DataFrame:
    dataframe = pd.DataFrame([transaction.to_dict() for transaction in transactions])
    if dataframe.empty:
        return dataframe
    dataframe["_statement_hash"] = file_hash
    dataframe["_statement_filename"] = filename
    dataframe["_issuer"] = issuer
    dataframe["_is_saved"] = is_saved
    return dataframe


def dataframe_from_database_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return dataframe
    dataframe["_statement_hash"] = dataframe["statement_hash"]
    dataframe["_statement_filename"] = dataframe["statement_filename"]
    dataframe["_issuer"] = dataframe["issuer"]
    dataframe["_is_saved"] = True
    return dataframe


def load_uploaded_transactions(uploaded_files, database: Database) -> tuple[pd.DataFrame, list[str]]:
    dataframes = []
    notes = []
    for uploaded_file in uploaded_files or []:
        content = uploaded_file.getvalue()
        file_hash = statement_fingerprint(content)
        if database.statement_exists(file_hash):
            stored = dataframe_from_database_rows(database.load_transactions(file_hash))
            dataframes.append(stored)
            notes.append(
                f"{uploaded_file.name}: already saved; loaded {len(stored)} transactions from history"
            )
            continue

        text = extract_text_from_pdf(content)
        issuer, transactions = parse_statement_text(text)
        parsed = dataframe_from_parsed_transactions(
            transactions,
            file_hash=file_hash,
            filename=uploaded_file.name,
            issuer=issuer,
            is_saved=False,
        )
        dataframes.append(parsed)
        notes.append(f"{uploaded_file.name}: {issuer} parser, {len(parsed)} transactions")

    populated = [dataframe for dataframe in dataframes if not dataframe.empty]
    return (pd.concat(populated, ignore_index=True) if populated else pd.DataFrame()), notes


def apply_local_llm(
    dataframe: pd.DataFrame,
    client: OllamaClient,
    *,
    auto_apply: bool,
    confidence_threshold: float,
) -> pd.DataFrame:
    updated = dataframe.copy()
    unknown_mask = updated["category"] == "Uncategorized"
    unknown_merchants = updated.loc[unknown_mask, "merchant"].dropna().astype(str).tolist()
    if not unknown_merchants:
        return updated

    with st.spinner(f"Classifying {len(set(unknown_merchants))} unknown merchant(s) locally..."):
        results = classify_merchants(unknown_merchants, client)
    for index in updated.index[unknown_mask]:
        merchant = str(updated.at[index, "merchant"])
        result = results[merchant]
        if auto_apply and result.category != "Uncategorized" and result.confidence >= confidence_threshold:
            updated.at[index, "category"] = result.category
            updated.at[index, "category_rule"] = (
                f"Local LLM: {result.model}/{result.prompt_version} "
                f"({result.confidence:.0%}) - {result.reason}"
            )
        else:
            updated.at[index, "category_rule"] = (
                f"Local LLM suggestion: {result.category} via "
                f"{result.model}/{result.prompt_version} "
                f"({result.confidence:.0%}) - {result.reason}"
            )
    return updated


def render_custom_rules() -> None:
    with st.expander("Custom Categories"):
        keyword = st.text_input("Merchant contains", placeholder="PARIS BAGUETTE")
        category = st.selectbox("Assign category", CATEGORIES[:-1])
        if st.button("Save rule", width="stretch", disabled=not keyword.strip()):
            add_custom_rule(keyword, category)
            st.success("Rule saved")
            st.rerun()

        saved_rules = list_custom_rules()
        if saved_rules:
            selected_index = st.selectbox(
                "Saved rules",
                range(len(saved_rules)),
                format_func=lambda index: f"{saved_rules[index][0]} -> {saved_rules[index][1]}",
            )
            if st.button("Delete selected rule", width="stretch"):
                saved_keyword, saved_category = saved_rules[selected_index]
                remove_custom_rule(saved_keyword, saved_category)
                st.rerun()


def render_authentication(database: Database) -> None:
    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        with st.container(horizontal_alignment="center", gap="xsmall"):
            st.image(str(APP_ICON_PATH), width=112)
            st.title("Credit Card Statement Analyzer", text_alignment="center")
            st.caption("Private access to your local spending history", text_alignment="center")

        if not database.has_users():
            with st.container(border=True):
                st.subheader("Create your local account")
                st.caption("This first account protects the data stored on this computer.")
                with st.form("create_local_account"):
                    display_name = st.text_input("Display name", placeholder="Eric Liu")
                    username = st.text_input("Username", placeholder="eric")
                    password = st.text_input("Password", type="password")
                    confirmation = st.text_input("Confirm password", type="password")
                    submitted = st.form_submit_button(
                        "Create account",
                        icon=":material/person_add:",
                        type="primary",
                        width="stretch",
                    )

                if submitted:
                    if password != confirmation:
                        st.error("The passwords do not match.", icon=":material/error:")
                    else:
                        try:
                            user = database.create_user(username, password, display_name)
                        except ValueError as error:
                            st.error(str(error), icon=":material/error:")
                        else:
                            st.session_state["authenticated"] = True
                            st.session_state["auth_user"] = user
                            st.rerun()
        else:
            with st.container(border=True):
                st.subheader("Sign in")
                with st.form("local_login"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button(
                        "Sign in",
                        icon=":material/login:",
                        type="primary",
                        width="stretch",
                    )

                if submitted:
                    user = database.authenticate_user(username, password)
                    if user is None:
                        st.error("Incorrect username or password.", icon=":material/error:")
                    else:
                        st.session_state["authenticated"] = True
                        st.session_state["auth_user"] = user
                        st.rerun()

        st.caption("Designed by Eric Liu", text_alignment="center")


def sign_out() -> None:
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


def render_history(database: Database) -> None:
    statements = database.list_statements()
    if not statements:
        st.info("No saved statements yet. Analyze a PDF and save the reviewed transactions first.")
        return

    statement_dataframe = pd.DataFrame(statements)
    st.subheader("Saved Statements")
    st.dataframe(
        statement_dataframe[
            [
                "filename",
                "issuer",
                "card_label",
                "statement_month",
                "transactions",
                "spending",
                "imported_at",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "filename": st.column_config.TextColumn("File"),
            "issuer": st.column_config.TextColumn("Issuer"),
            "card_label": st.column_config.TextColumn("Card"),
            "statement_month": st.column_config.TextColumn("Statement month"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "spending": st.column_config.NumberColumn("Spending", format="$%.2f"),
            "imported_at": st.column_config.DatetimeColumn("Imported", format="MMM DD, YYYY h:mm a"),
        },
    )

    history = prepare_dataframe(dataframe_from_database_rows(database.load_transactions()))
    available_cards = sorted(history["card"].dropna().unique())
    with st.sidebar:
        selected_cards = st.multiselect(
            "Cards",
            available_cards,
            default=available_cards,
            key="history_cards",
        )
    if selected_cards:
        history = history[history["card"].isin(selected_cards)]
    history = render_month_filter(history, "history_months")
    render_dashboard(history)

    st.subheader("Saved Transactions")
    st.dataframe(
        history[
            [
                "date",
                "merchant",
                "amount",
                "category",
                "category_rule",
                "card",
                "statement_filename",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "statement_filename": st.column_config.TextColumn("Statement"),
        },
    )

    with st.expander("Delete a saved statement"):
        options = {int(row["id"]): f"{row['filename']} · {row['card_label']}" for row in statements}
        statement_id = st.selectbox(
            "Statement",
            list(options),
            format_func=options.get,
        )
        confirmed = st.checkbox("I understand this also deletes its saved transactions.")
        if st.button(
            "Delete statement",
            icon=":material/delete:",
            disabled=not confirmed,
        ):
            database.delete_statement(statement_id)
            st.success("Statement deleted")
            st.rerun()


def render_analyzer(database: Database) -> None:
    llm_client = OllamaClient()
    llm_ready = llm_client.is_ready()

    with st.sidebar:
        st.header("Statements")
        uploaded_files = st.file_uploader(
            "Upload PDF statements",
            type=["pdf"],
            accept_multiple_files=True,
        )
        use_sample_data = st.toggle("Use sample data", value=not uploaded_files)
        if uploaded_files:
            st.caption(f"{len(uploaded_files)} statement(s) selected")

        render_custom_rules()

        st.header("Local AI")
        use_local_llm = st.toggle(
            "Classify unknown merchants",
            value=llm_ready,
            disabled=not llm_ready,
        )
        auto_apply_llm = st.toggle(
            "Auto-apply high-confidence results",
            value=False,
            disabled=not llm_ready or not use_local_llm,
        )
        confidence_threshold = st.slider(
            "Minimum confidence",
            min_value=0.50,
            max_value=1.00,
            value=0.80,
            step=0.05,
            disabled=not llm_ready,
        )
        st.caption(f"{DEFAULT_MODEL}: {'ready' if llm_ready else 'not available'}")

    if use_sample_data:
        dataframe = sample_transactions()
        dataframe["original_description"] = dataframe["merchant"]
        for column in INTERNAL_COLUMNS:
            dataframe[column] = None if column != "_is_saved" else True
        notes = ["Sample data loaded; sample transactions cannot be saved"]
    else:
        dataframe, notes = load_uploaded_transactions(uploaded_files, database)

    for note in notes:
        st.caption(note)
    if dataframe.empty:
        st.info("Upload a PDF statement or turn on sample data to begin.")
        return

    dataframe = prepare_dataframe(dataframe)
    if use_local_llm:
        try:
            dataframe = apply_local_llm(
                dataframe,
                llm_client,
                auto_apply=auto_apply_llm,
                confidence_threshold=confidence_threshold,
            )
        except (OSError, TimeoutError, ValueError, KeyError) as error:
            st.warning(f"Local AI classification was unavailable: {error}")

    st.subheader("Review Transactions")
    editor_columns = [
        "date",
        "merchant",
        "amount",
        "category",
        "category_rule",
        "card",
        "original_description",
        *INTERNAL_COLUMNS,
    ]
    edited = st.data_editor(
        dataframe[editor_columns],
        key="transaction_editor",
        num_rows="fixed",
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "merchant": st.column_config.TextColumn("Merchant"),
            "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES),
            "category_rule": st.column_config.TextColumn("Rule source"),
            "card": st.column_config.TextColumn("Card"),
            "original_description": None,
            "_statement_hash": None,
            "_statement_filename": None,
            "_issuer": None,
            "_is_saved": None,
        },
        disabled=["category_rule", "card", "original_description", *INTERNAL_COLUMNS],
    )
    edited = prepare_dataframe(edited)

    unsaved = edited[
        edited["_statement_hash"].notna() & ~edited["_is_saved"].fillna(False).astype(bool)
    ]
    save_disabled = use_sample_data or unsaved.empty
    if st.button(
        "Save reviewed transactions to history",
        icon=":material/save:",
        type="primary",
        disabled=save_disabled,
    ):
        saved_count = 0
        for file_hash, group in unsaved.groupby("_statement_hash", sort=False):
            inserted = database.save_statement(
                file_hash=str(file_hash),
                filename=str(group["_statement_filename"].iloc[0]),
                issuer=str(group["_issuer"].iloc[0]),
                transactions=group.to_dict("records"),
            )
            saved_count += int(inserted)
        if saved_count:
            st.success(f"Saved {saved_count} statement(s) to history.")
        else:
            st.info("These statements were already saved.")
        st.rerun()
    elif not use_sample_data and save_disabled:
        st.caption("All uploaded statements are already saved in history.")

    filtered = render_month_filter(edited, "analysis_months")
    render_dashboard(filtered)

    csv_data = edited.drop(columns=["month", *INTERNAL_COLUMNS]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export CSV",
        csv_data,
        "transactions.csv",
        "text/csv",
        icon=":material/download:",
    )


st.set_page_config(
    page_title="Credit Card Statement Analyzer",
    page_icon=str(APP_ICON_PATH),
    layout="wide",
)
st.logo(str(APP_ICON_PATH), size="large")

database = get_database(str(default_database_path()))
if not st.session_state.get("authenticated"):
    render_authentication(database)
    st.stop()

st.title("Credit Card Statement Analyzer")
with st.sidebar:
    user = st.session_state.get("auth_user", {})
    st.caption(f"Signed in as {user.get('display_name', user.get('username', 'Local user'))}")
    if st.button(
        "Sign out",
        icon=":material/logout:",
        width="stretch",
    ):
        sign_out()
    section = st.segmented_control(
        "Workspace",
        ["Analyze", "History"],
        default="Analyze",
        width="stretch",
    )
    st.caption("Designed by Eric Liu")

if section == "History":
    render_history(database)
else:
    render_analyzer(database)
