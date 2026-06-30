window.ARMCARE_BENCHMARK = {
  "project": "ArmCare Edge Triage",
  "generated_at_utc": "2026-06-30T02:43:37Z",
  "claim_boundary": "Synthetic care-intake routing benchmark. Not medical diagnosis. No external API or patient data used.",
  "git_commit": "cfb6839",
  "platform": {
    "machine": "arm64",
    "processor": "arm",
    "platform": "Darwin-25.2.0-arm64-arm-64bit-Mach-O",
    "python": "3.14.4",
    "numpy": "2.4.2",
    "mac_model": "Mac16,1",
    "cpu_brand": "Apple M4"
  },
  "dataset": {
    "samples": 12000,
    "features": 192,
    "classes": [
      "urgent_care",
      "access_support",
      "paperwork",
      "routine_followup"
    ],
    "class_counts": {
      "urgent_care": 2964,
      "access_support": 2970,
      "paperwork": 3064,
      "routine_followup": 3002
    },
    "seed": 260630
  },
  "baseline": {
    "name": "fp32_single_ticket_probability",
    "median_ms": 78.98854196537286,
    "runs_ms": [
      105.09525006636977,
      78.98854196537286,
      111.62574996706098,
      58.56649996712804,
      96.03095799684525,
      64.99420793261379,
      59.69699996057898
    ],
    "accuracy": 1.0,
    "tickets_per_second": 151920.76852438398
  },
  "optimized": {
    "name": "int8_arm_batch",
    "median_ms": 3.7337499670684338,
    "runs_ms": [
      4.597957944497466,
      4.0959169855341315,
      3.7337499670684338,
      3.337583038955927,
      3.2892079325392842,
      4.193375003524125,
      3.405833966098726
    ],
    "accuracy": 1.0,
    "agreement_with_baseline": 1.0,
    "feature_scale": 0.03650276304229977,
    "weight_scale": 0.024435910652941605,
    "tickets_per_second": 3213927.04542073
  },
  "speedup": 21.155284275071846,
  "memory": {
    "baseline_bytes": 9219088,
    "optimized_bytes": 2304784,
    "reduction_percent": 74.99986983528089
  },
  "sample_tickets": [
    {
      "queue": "urgent_care",
      "message": "Patient reports chest tightness and dizziness after new medication."
    },
    {
      "queue": "urgent_care",
      "message": "Caregiver says fever has returned and breathing sounds worse tonight."
    },
    {
      "queue": "access_support",
      "message": "Need wheelchair access and quiet waiting room for next appointment."
    },
    {
      "queue": "access_support",
      "message": "Client asks for an interpreter and written instructions in advance."
    },
    {
      "queue": "paperwork",
      "message": "Please prepare the disability certificate renewal documents this week."
    },
    {
      "queue": "paperwork",
      "message": "Insurance office needs a signed treatment summary and visit history."
    },
    {
      "queue": "routine_followup",
      "message": "Can we move the checkup from Tuesday morning to Friday afternoon?"
    },
    {
      "queue": "routine_followup",
      "message": "Confirm whether the next remote follow-up link is still valid."
    }
  ]
};
