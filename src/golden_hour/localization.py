from __future__ import annotations

def detect_language(text: str) -> str:
    """Conservative UI-language choice; never transliterates financial identifiers."""
    if any("\u0900" <= char <= "\u097f" for char in text):
        return "hi"
    hinglish_markers = ("mujhe", "mere", "paise", "fraud hua", "bank ko", "madad", "kya karu")
    if any(marker in text.lower() for marker in hinglish_markers):
        return "hinglish"
    return "en"

def urgent_guidance(language: str) -> str:
    if language == "hi":
        return "अगर पैसे हाल में गए हैं: अपने बैंक के सत्यापित आधिकारिक चैनल से तुरंत संपर्क करें और भारत की आधिकारिक वित्तीय-धोखाधड़ी रिपोर्टिंग सुविधा (1930/NCRP) का उपयोग करें। OTP, PIN, CVV या पासवर्ड साझा न करें और कोई APK इंस्टॉल/चलाएँ नहीं। मैं जानकारी व्यवस्थित करने में मदद कर सकता हूँ; पैसे रोकने या वापसी की गारंटी नहीं दे सकता।"
    if language == "hinglish":
        return "Agar paise recently gaye hain: apne bank ke verified official channel se turant contact karein aur India ki official financial-fraud reporting facility (1930/NCRP) use karein. OTP, PIN, CVV ya password share na karein, aur koi APK install/run na karein. Main facts organize karne mein help kar sakta hoon; paise freeze ya recovery guarantee nahi kar sakta."
    return "If money may have moved recently: contact your bank through its verified official channel and use India's official financial-fraud reporting route (1930/NCRP). Do not share OTPs, PINs, CVV, passwords, or install/execute an APK. I can help prepare facts; I cannot freeze funds or guarantee recovery."
