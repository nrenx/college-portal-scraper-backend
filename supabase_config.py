#!/usr/bin/env python3
"""
Supabase Configuration for Fast Uploader

This file contains configuration settings for the Supabase uploader.
"""

# Supabase credentials
SUPABASE_URL = "https://ndeagjkuhzyozgimudow.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5kZWFnamt1aHp5b3pnaW11ZG93Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDg5OTY4NiwiZXhwIjoyMDYwNDc1Njg2fQ.qyjFWHusv_o03P_eS_j_kCemXLD45wvioD3lxIqYlbM"

# Default settings
DEFAULT_SETTINGS = {
    # Storage settings
    "bucket": "demo-usingfastapi",
    "source_dir": "student_details",

    # Performance settings
    "workers": 32,

    # Feature settings
    "skip_existing": True,
}
