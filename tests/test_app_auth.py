from streamlit.testing.v1 import AppTest


def test_first_run_account_login_and_logout(tmp_path, monkeypatch):
    monkeypatch.setenv("CCSA_DATA_DIR", str(tmp_path))
    app = AppTest.from_file("app.py")

    app.run(timeout=30)
    assert len(app.exception) == 0
    assert app.subheader[0].value == "Create your local account"
    assert "Designed by Eric Liu" in [caption.value for caption in app.caption]

    app.text_input[0].set_value("Eric Liu")
    app.text_input[1].set_value("eric")
    app.text_input[2].set_value("secure-pass-2026")
    app.text_input[3].set_value("secure-pass-2026")
    app.button[0].click().run(timeout=30)

    assert len(app.exception) == 0
    assert app.segmented_control[0].value == "Analyze"
    assert "Sign out" in [button.label for button in app.button]

    next(button for button in app.button if button.label == "Sign out").click().run(timeout=30)
    assert len(app.exception) == 0
    assert app.subheader[0].value == "Sign in"

    app.text_input[0].set_value("eric")
    app.text_input[1].set_value("secure-pass-2026")
    app.button[0].click().run(timeout=30)

    assert len(app.exception) == 0
    assert app.segmented_control[0].value == "Analyze"
