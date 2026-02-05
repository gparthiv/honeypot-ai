#!/usr/bin/env python3
"""
Multi-Turn Honeypot Test Script
Tests intelligence extraction and tricking capabilities
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/honeypot"
API_KEY = "test@123"
SESSION_ID = f"test-bank-fraud-{int(time.time())}"

# Test conversation - Bank Fraud Scam in Hinglish
CONVERSATION = [
    # Turn 1: Initial scam
    "Aapka bank account block ho jayega. Immediately verify karo.",
    
    # Turn 2: More urgency
    "Sir, account suspend hone wala hai. Last warning hai ye.",
    
    # Turn 3: Request details
    "Apna account number aur UPI ID verify karne ke liye share karo.",
    
    # Turn 4: Scammer reveals phone
    "Call karo is number pe: 9876543210. Confirm karna hai details.",
    
    # Turn 5: Scammer reveals bank account
    "Payment verification ke liye Rs 100 send karo account 123456789012 pe.",
    
    # Turn 6: Scammer reveals UPI
    "Ya phir UPI se bhi bhej sakte ho: scammer@paytm pe.",
    
    # Turn 7: Phishing link
    "Verify karne ke liye is link pe jao: https://fake-sbi-verify.com/login",
    
    # Turn 8: More pressure
    "Jaldi karo! 10 minute mein account permanently block ho jayega!",
    
    # Turn 9: Alternative contact
    "Emergency helpline: 9123456789. Turant call karo.",
    
    # Turn 10: Email address
    "Ya email karo helpdesk@fakesbi.com pe. Urgent hai!",
    
    # Turn 11: Name and location
    "Main Rajesh Kumar, RBI officer. Delhi office se call kar raha hoon. Pincode 110001.",
    
    # Turn 12: IFSC code
    "Last chance! IFSC code HDFC0001234 use karke payment karo immediately!"
]

def send_message(turn, message):
    """Send a message and display response"""
    print("\n" + "="*70)
    print(f"TURN {turn}")
    print("="*70)
    print(f"🎭 Scammer: {message}")
    
    payload = {
        "sessionId": SESSION_ID,
        "message": {
            "text": message,
            "sender": "scammer",
            "timestamp": int(time.time() * 1000)
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Display agent reply
            print(f"🤖 Agent: {data.get('reply', 'NO REPLY')}")
            
            # Display detection info
            print(f"\n📊 Detection:")
            print(f"   Scam: {data.get('scamDetected', False)}")
            print(f"   Confidence: {data.get('confidence', 0)}")
            print(f"   Language: {data.get('languageDetected', 'N/A')}")
            print(f"   Turn: {data.get('sessionTurns', 0)}")
            
            # Display extracted intelligence
            intel = data.get('extractedIntelligence', {})
            extracted = []
            
            for key, values in intel.items():
                if values:
                    extracted.append(f"{key}: {values}")
            
            if extracted:
                print(f"\n🔍 EXTRACTED THIS TURN:")
                for item in extracted:
                    print(f"   ✓ {item}")
            
            # Display keywords
            keywords = data.get('keywords', [])
            if keywords:
                print(f"\n🏷️  Keywords: {', '.join(keywords)}")
            
            return data
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Run the test conversation"""
    print("\n" + "="*70)
    print("  ENHANCED HONEYPOT - MULTI-TURN INTELLIGENCE EXTRACTION TEST")
    print("="*70)
    print(f"\nSession ID: {SESSION_ID}")
    print(f"Testing {len(CONVERSATION)} conversation turns...")
    print("\nThis test will:")
    print("  • Detect scam patterns")
    print("  • Extract intelligence (phones, accounts, UPI, URLs, emails, names)")
    print("  • Show tricking tactics in action")
    print("  • Trigger GUVI callback after turn 8")
    
    # Run conversation
    all_intel = {
        "phoneNumbers": set(),
        "bankAccounts": set(),
        "upiIds": set(),
        "phishingLinks": set(),
        "emailAddresses": set(),
        "scammerNames": set(),
        "pincodes": set(),
        "ifscCodes": set()
    }
    
    for turn, message in enumerate(CONVERSATION, 1):
        result = send_message(turn, message)
        
        if result:
            # Accumulate intelligence
            intel = result.get('extractedIntelligence', {})
            for key in all_intel:
                if key in intel:
                    all_intel[key].update(intel[key])
        
        time.sleep(1)  # Pause between turns
    
    # Final summary
    print("\n" + "="*70)
    print("  FINAL INTELLIGENCE SUMMARY")
    print("="*70)
    
    total_extracted = 0
    
    print("\n📊 Accumulated Intelligence:")
    for key, values in all_intel.items():
        if values:
            print(f"\n   {key}:")
            for value in values:
                print(f"      • {value}")
                total_extracted += 1
    
    print(f"\n🎯 Total Items Extracted: {total_extracted}")
    
    # Expected extractions
    print("\n✅ Expected Extractions:")
    print("   • Phone Numbers: 9876543210, 9123456789")
    print("   • Bank Account: 123456789012")
    print("   • UPI ID: scammer@paytm")
    print("   • Phishing Link: https://fake-sbi-verify.com/login")
    print("   • Email: helpdesk@fakesbi.com")
    print("   • Scammer Name: Rajesh Kumar")
    print("   • Pincode: 110001")
    print("   • IFSC Code: HDFC0001234")
    
    print("\n💡 Notes:")
    print("   • GUVI callback should have been sent after turn 8")
    print("   • Check server logs for callback confirmation")
    print("   • Agent should have shown Hinglish responses")
    print("   • Tricking tactics should be visible in agent replies")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
