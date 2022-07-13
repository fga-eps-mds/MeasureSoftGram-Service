from _src.app import create_app

if __name__ == "__main__":
    app, _, _ = create_app()
    app.run(host="0.0.0.0", debug=True)
