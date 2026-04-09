"""
Seed data generator for CivicPulse.
Creates 15 realistic community needs + 20 volunteers with varied skills.
Run: python seed_data.py (from /backend directory)
"""

import sys
import os
import json
import logging
import random

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def seed():
    from app.db.database import SessionLocal
    from app.db.init_db import init_db
    from app.models.need import Need
    from app.models.volunteer import Volunteer
    from app.services.embedding_service import embed_need, embed_volunteer
    from app.services.ranking_service import calculate_urgency_score

    init_db()
    db = SessionLocal()

    # ── Volunteers ──────────────────────────────────────────────────────────────
    volunteer_data = [
        {"name": "James Okonkwo",    "email": "james@cv.local",    "skills_raw": "carpentry roofing construction home repair decking", "lat": 12.9716, "lng": 77.5946},
        {"name": "Sarah Matthews",   "email": "sarah@cv.local",    "skills_raw": "social work mental health counseling family support crisis intervention", "lat": 12.9780, "lng": 77.6080},
        {"name": "Marcus Chen",      "email": "marcus@cv.local",   "skills_raw": "driving logistics transport delivery food distribution", "lat": 12.9650, "lng": 77.5890},
        {"name": "Priya Sharma",     "email": "priya@cv.local",    "skills_raw": "nursing first aid healthcare medication management elder care", "lat": 12.9700, "lng": 77.6100},
        {"name": "David Williams",   "email": "david@cv.local",    "skills_raw": "plumbing electrical engineering maintenance facility management", "lat": 12.9800, "lng": 77.5800},
        {"name": "Lisa Park",        "email": "lisa@cv.local",     "skills_raw": "teaching tutoring education childcare literacy programs youth", "lat": 12.9720, "lng": 77.5950},
        {"name": "Roberto Garcia",   "email": "roberto@cv.local",  "skills_raw": "legal aid housing advocacy tenant rights immigration support", "lat": 12.9740, "lng": 77.6020},
        {"name": "Emma Thompson",    "email": "emma@cv.local",     "skills_raw": "cooking food preparation meal planning nutrition catering", "lat": 12.9690, "lng": 77.5920},
        {"name": "Ahmed Hassan",     "email": "ahmed@cv.local",    "skills_raw": "IT computer repair tech support software setup digital literacy", "lat": 12.9760, "lng": 77.5960},
        {"name": "Maria Gonzalez",   "email": "maria@cv.local",    "skills_raw": "Spanish translation interpretation community outreach multilingual", "lat": 12.9710, "lng": 77.6050},
        {"name": "Tom Richardson",   "email": "tom@cv.local",      "skills_raw": "painting drywall flooring renovation property maintenance", "lat": 12.9830, "lng": 77.5870},
        {"name": "Ananya Reddy",     "email": "ananya@cv.local",   "skills_raw": "physical therapy rehabilitation mobility senior wellness exercise", "lat": 12.9670, "lng": 77.5930},
        {"name": "Kevin Osei",       "email": "kevin@cv.local",    "skills_raw": "job counseling resume writing career coaching employment support", "lat": 12.9750, "lng": 77.6000},
        {"name": "Jennifer Walsh",   "email": "jennifer@cv.local", "skills_raw": "accounting financial counseling budgeting benefits assistance", "lat": 12.9800, "lng": 77.5960},
        {"name": "Raj Patel",        "email": "raj@cv.local",      "skills_raw": "carpentry woodworking furniture repair general handyman tools", "lat": 12.9725, "lng": 77.5970},
        {"name": "Nina Browne",      "email": "nina@cv.local",     "skills_raw": "gardening landscaping urban farming food growing sustainability", "lat": 12.9690, "lng": 77.5990},
        {"name": "Carlos Vega",      "email": "carlos@cv.local",   "skills_raw": "driving truck heavy lifting moving furniture storage physical labor", "lat": 12.9760, "lng": 77.5860},
        {"name": "Fatima Al-Rashid", "email": "fatima@cv.local",   "skills_raw": "Arabic translation community health worker outreach refugee support", "lat": 12.9740, "lng": 77.6040},
        {"name": "Daniel Kim",       "email": "daniel@cv.local",   "skills_raw": "photography videography documentation storytelling media communication", "lat": 12.9780, "lng": 77.5910},
        {"name": "Grace Oduya",      "email": "grace@cv.local",    "skills_raw": "child development daycare early education parenting support social services", "lat": 12.9710, "lng": 77.6060},
    ]

    availability_templates = [
        {"monday": True, "wednesday": True, "friday": True},
        {"saturday": True, "sunday": True},
        {"tuesday": True, "thursday": True, "saturday": True},
        {"weekdays": True},
        {"anytime": True},
    ]

    logger.info(f"Seeding {len(volunteer_data)} volunteers...")
    for vd in volunteer_data:
        if db.query(Volunteer).filter(Volunteer.email == vd["email"]).first():
            continue
        skills_list = vd["skills_raw"].split()
        availability = random.choice(availability_templates)
        embedding = embed_volunteer({"skills_raw": vd["skills_raw"], "skills_list": skills_list})
        vol = Volunteer(
            name=vd["name"],
            email=vd["email"],
            phone=f"+1555{random.randint(1000000, 9999999)}",
            skills_raw=vd["skills_raw"],
            skills_list=skills_list,
            availability=availability,
            transport_available=random.choice([True, False]),
            latitude=vd["lat"],
            longitude=vd["lng"],
            willing_distance_km=random.choice([5.0, 10.0, 15.0, 20.0]),
            total_tasks_completed=random.randint(0, 25),
            average_rating=round(random.uniform(3.5, 5.0), 1),
            embedding=embedding,
        )
        db.add(vol)
    db.commit()
    logger.info("✓ Volunteers seeded")

    # ── Community Needs ──────────────────────────────────────────────────────────
    needs_data = [
        {
            "raw_input": "Mrs. Chen, 67, roof started leaking 2 weeks ago during rain. Lives at 245 Oak St, Apt 3B, District 5. Mold risk. Can't afford contractor. Neighbor Raj offered to help but needs tools.",
            "need_type": "Home Repair",
            "need_subtype": "Structural - Roof",
            "location_address": "245 Oak St, Apt 3B",
            "location_district": "District 5",
            "urgency": "HIGH",
            "urgency_reason": "Active water damage; mold risk imminent if it rains again",
            "skills_needed": ["carpentry", "roofing"],
            "affected_population": 1,
            "resource_gaps": "Tools + second labor hand",
            "estimated_effort_hours": 6.0,
            "escalation_risk": 0.75,
            "confidence_score": 0.96,
        },
        {
            "raw_input": "Family of 4 in District 5 has not had food for 2 days. Father lost job, mother is ill. Kids ages 4 and 7. They need grocery delivery ASAP.",
            "need_type": "Food",
            "need_subtype": "Emergency Food Assistance",
            "location_address": "78 Elm Road",
            "location_district": "District 5",
            "urgency": "CRITICAL",
            "urgency_reason": "Children without food for 48+ hours; immediate nutrition crisis",
            "skills_needed": ["food delivery", "logistics"],
            "affected_population": 4,
            "resource_gaps": "Food supply + delivery vehicle",
            "estimated_effort_hours": 2.0,
            "escalation_risk": 0.95,
            "confidence_score": 0.98,
        },
        {
            "raw_input": "Duplicate: Another family at 82 Elm Rd, District 5 also needs food. Kids are hungry. Please send someone today.",
            "need_type": "Food",
            "need_subtype": "Emergency Food Assistance",
            "location_address": "82 Elm Road",
            "location_district": "District 5",
            "urgency": "CRITICAL",
            "urgency_reason": "Duplicate report of food crisis in same block",
            "skills_needed": ["food delivery"],
            "affected_population": 3,
            "resource_gaps": "Food supply",
            "estimated_effort_hours": 1.5,
            "escalation_risk": 0.90,
            "confidence_score": 0.85,
        },
        {
            "raw_input": "Single mother, District 7. Eviction notice served yesterday. Has 2 children ages 6 and 9. No savings, no shelter. Needs emergency housing TODAY.",
            "need_type": "Housing",
            "need_subtype": "Emergency Shelter",
            "location_address": "113 Pine Ave",
            "location_district": "District 7",
            "urgency": "CRITICAL",
            "urgency_reason": "Eviction imminent; family with children at risk of homelessness tonight",
            "skills_needed": ["housing advocacy", "legal aid", "social work"],
            "affected_population": 3,
            "resource_gaps": "Emergency shelter + legal representation",
            "estimated_effort_hours": 8.0,
            "escalation_risk": 0.95,
            "confidence_score": 0.97,
        },
        {
            "raw_input": "Mr. Kofi, 72, diabetic. Lives alone District 3. No transport to hospital for insulin. Appointment is tomorrow morning. Very worried.",
            "need_type": "Health",
            "need_subtype": "Medical Transport",
            "location_address": "34 Cedar Lane, District 3",
            "location_district": "District 3",
            "urgency": "HIGH",
            "urgency_reason": "Diabetic patient needs transport to medical appointment; missing insulin could be life-threatening",
            "skills_needed": ["driving", "transport"],
            "affected_population": 1,
            "resource_gaps": "Transportation to clinic",
            "estimated_effort_hours": 3.0,
            "escalation_risk": 0.80,
            "confidence_score": 0.95,
        },
        {
            "raw_input": "Youth center District 2 needs math tutor, Tuesdays/Thursdays 4-6pm. 8 kids ages 10-14 falling behind. No cost for families.",
            "need_type": "Job Training",
            "need_subtype": "Youth Education",
            "location_address": "Youth Center, District 2",
            "location_district": "District 2",
            "urgency": "MEDIUM",
            "urgency_reason": "Academic performance declining; ongoing need",
            "skills_needed": ["teaching", "tutoring", "mathematics"],
            "affected_population": 8,
            "resource_gaps": "Qualified math tutor 2x/week",
            "estimated_effort_hours": 4.0,
            "escalation_risk": 0.40,
            "confidence_score": 0.92,
        },
        {
            "raw_input": "Elderly woman, 81, District 4, has not left home in 3 weeks. Neighbor says she seems confused and sad. May need welfare check and mental health support.",
            "need_type": "Mental Health",
            "need_subtype": "Elderly Isolation",
            "location_address": "District 4",
            "location_district": "District 4",
            "urgency": "HIGH",
            "urgency_reason": "Possible cognitive decline and social isolation; no family contact",
            "skills_needed": ["social work", "mental health", "elder care"],
            "affected_population": 1,
            "resource_gaps": "Welfare check + ongoing social support",
            "estimated_effort_hours": 2.0,
            "escalation_risk": 0.70,
            "confidence_score": 0.88,
        },
        {
            "raw_input": "Pipes burst in apartment building, District 6. 12 families affected. No running water. Landlord unreachable. Plumber needed urgently.",
            "need_type": "Home Repair",
            "need_subtype": "Plumbing Emergency",
            "location_address": "22 Maple Street, District 6",
            "location_district": "District 6",
            "urgency": "CRITICAL",
            "urgency_reason": "No running water for 12 families; hygiene and health emergency",
            "skills_needed": ["plumbing", "maintenance", "engineering"],
            "affected_population": 36,
            "resource_gaps": "Licensed plumber + parts",
            "estimated_effort_hours": 8.0,
            "escalation_risk": 0.92,
            "confidence_score": 0.97,
        },
        {
            "raw_input": "Refugee family, 5 members, District 8. Arabic speaking only. Need help understanding their rights and accessing city services. Very stressed.",
            "need_type": "Other",
            "need_subtype": "Refugee Support / Translation",
            "location_address": "District 8",
            "location_district": "District 8",
            "urgency": "MEDIUM",
            "urgency_reason": "Language barrier preventing access to essential services",
            "skills_needed": ["Arabic translation", "community outreach", "legal aid"],
            "affected_population": 5,
            "resource_gaps": "Arabic interpreter + case worker",
            "estimated_effort_hours": 4.0,
            "escalation_risk": 0.55,
            "confidence_score": 0.90,
        },
        {
            "raw_input": "Food drive needed at community center, District 2, Saturday. Need 5 volunteers to sort + pack 200 food boxes for distribution to local families.",
            "need_type": "Food",
            "need_subtype": "Food Drive Logistics",
            "location_address": "Community Center, District 2",
            "location_district": "District 2",
            "urgency": "MEDIUM",
            "urgency_reason": "Event-based need; Saturday deadline",
            "skills_needed": ["food preparation", "logistics", "driving"],
            "affected_population": 200,
            "resource_gaps": "5 volunteers for 4-hour shift",
            "estimated_effort_hours": 4.0,
            "escalation_risk": 0.30,
            "confidence_score": 0.95,
        },
        {
            "raw_input": "Mr. Thompson, District 1, unemployed 6 months. Needs help writing resume and preparing for interviews. Background in construction.",
            "need_type": "Job Training",
            "need_subtype": "Employment Support",
            "location_address": "District 1",
            "location_district": "District 1",
            "urgency": "LOW",
            "urgency_reason": "Long-term stability need; not an emergency",
            "skills_needed": ["career coaching", "resume writing"],
            "affected_population": 1,
            "resource_gaps": "Job counselor",
            "estimated_effort_hours": 3.0,
            "escalation_risk": 0.30,
            "confidence_score": 0.94,
        },
        {
            "raw_input": "Teen girl, 16, District 9, showing signs of depression. Parents unavailable. School social worker flagged. Needs mental health counseling.",
            "need_type": "Mental Health",
            "need_subtype": "Youth Mental Health",
            "location_address": "District 9",
            "location_district": "District 9",
            "urgency": "HIGH",
            "urgency_reason": "Adolescent showing depression symptoms; no supportive adults present",
            "skills_needed": ["mental health", "counseling", "youth work"],
            "affected_population": 1,
            "resource_gaps": "Youth mental health counselor",
            "estimated_effort_hours": 2.0,
            "escalation_risk": 0.75,
            "confidence_score": 0.91,
        },
        {
            "raw_input": "Community garden District 3 needs volunteers for planting weekend. 20 plots to maintain. Supplies available. Good for families.",
            "need_type": "Other",
            "need_subtype": "Community Garden",
            "location_address": "Community Garden, District 3",
            "location_district": "District 3",
            "urgency": "LOW",
            "urgency_reason": "Seasonal planting window; not urgent",
            "skills_needed": ["gardening", "landscaping"],
            "affected_population": 50,
            "resource_gaps": "10 volunteers for 3-hour day",
            "estimated_effort_hours": 3.0,
            "escalation_risk": 0.15,
            "confidence_score": 0.98,
        },
        {
            "raw_input": "Elderly couple District 5, ages 75 and 78. No family. Weekly grocery run needed. Husband has mobility issues.",
            "need_type": "Transport",
            "need_subtype": "Grocery Transport",
            "location_address": "District 5",
            "location_district": "District 5",
            "urgency": "MEDIUM",
            "urgency_reason": "Regular weekly need; mobility limitations prevent self-service",
            "skills_needed": ["driving", "elder care"],
            "affected_population": 2,
            "resource_gaps": "Driver with car once a week",
            "estimated_effort_hours": 2.0,
            "escalation_risk": 0.40,
            "confidence_score": 0.93,
        },
        {
            "raw_input": "Water damage to community library District 4. Ceiling collapsed in reading room after storm. Books + furniture need removal and cleanup.",
            "need_type": "Home Repair",
            "need_subtype": "Storm Damage Cleanup",
            "location_address": "District 4 Library",
            "location_district": "District 4",
            "urgency": "HIGH",
            "urgency_reason": "Structural damage; building closed; community resource unavailable",
            "skills_needed": ["carpentry", "painting", "physical labor"],
            "affected_population": 150,
            "resource_gaps": "Contractors + cleanup crew",
            "estimated_effort_hours": 12.0,
            "escalation_risk": 0.65,
            "confidence_score": 0.94,
        },
    ]

    logger.info(f"Seeding {len(needs_data)} community needs...")
    for nd in needs_data:
        # Skip if raw_input already exists
        if db.query(Need).filter(Need.raw_input == nd["raw_input"]).first():
            continue

        embedding = embed_need(nd)
        need = Need(
            raw_input=nd["raw_input"],
            need_type=nd.get("need_type"),
            need_subtype=nd.get("need_subtype"),
            location_address=nd.get("location_address"),
            location_district=nd.get("location_district"),
            urgency=nd.get("urgency", "MEDIUM"),
            urgency_reason=nd.get("urgency_reason"),
            skills_needed=nd.get("skills_needed", []),
            affected_population=nd.get("affected_population", 1),
            resource_gaps=nd.get("resource_gaps"),
            estimated_effort_hours=nd.get("estimated_effort_hours"),
            escalation_risk=nd.get("escalation_risk", 0.5),
            confidence_score=nd.get("confidence_score", 0.8),
            status="open",
            report_count=1,
            embedding=embedding,
        )
        from app.services.ranking_service import calculate_urgency_score
        need.urgency_score = calculate_urgency_score(need)
        db.add(need)

    db.commit()
    logger.info("✓ Community needs seeded")

    # Summary
    total_vols = db.query(Volunteer).count()
    total_needs = db.query(Need).count()
    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Seed complete: {total_vols} volunteers, {total_needs} needs")
    logger.info(f"{'='*50}\n")
    db.close()


if __name__ == "__main__":
    seed()
