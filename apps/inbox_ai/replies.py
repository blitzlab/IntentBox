SUGGESTIONS = {
  "booking_inquiry": ["Hi! Yes, it’s available. Check-in is 2pm. How many nights?"],
  "checkin_help":    ["Sorry about that. Here’s the key box code: ####. Need a walkthrough?"],
  "payment_issue":   ["I’m sorry for the charge issue. Please share the last 4 digits and date; I’ll escalate."],
  "complaint":       ["Thanks for flagging this. I can offer a cleaner visit now or a partial refund—your call."],
  "chit_chat":       ["Thanks! If you need anything during your stay, I’m here."]
}
def suggestions_for_intent(intent: str):
    return SUGGESTIONS.get(intent, ["Thanks for reaching out—how can I help?"])