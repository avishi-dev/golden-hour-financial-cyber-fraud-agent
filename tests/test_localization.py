from golden_hour.localization import detect_language, urgent_guidance

def test_detects_hindi_and_hinglish():
    assert detect_language("मेरे पैसे चले गए हैं") == "hi"
    assert detect_language("Mujhe fraud hua hai, kya karu?") == "hinglish"
    assert detect_language("I need help with a suspicious transfer") == "en"

def test_hindi_guidance_does_not_make_recovery_promises():
    text = urgent_guidance("hi")
    assert "1930" in text
    assert "गारंटी" in text
