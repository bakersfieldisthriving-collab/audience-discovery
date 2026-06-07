from audience_discovery.crawl.extract import extract_signals, parse_html


def test_extract_public_sponsor_email_and_platform() -> None:
    html = """
    <html>
      <head>
        <title>Healthspan Lab Newsletter</title>
        <meta name="description" content="A longevity newsletter for 12,000 readers.">
      </head>
      <body>
        <p>Advertise with us or request our media kit.</p>
        <p>Business inquiries: sponsor@healthspan.example</p>
        <a href="https://youtube.com/@healthspanlab">YouTube</a>
      </body>
    </html>
    """
    page = parse_html("https://healthspan.example/advertise", html)
    signals = extract_signals(page)

    assert signals.sponsor_signal == "media_kit"
    assert signals.contact_method == "public_email"
    assert signals.public_contact == "sponsor@healthspan.example"
    assert signals.platform == "youtube"
