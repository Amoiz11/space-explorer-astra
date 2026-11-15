-- Seed data for Celestial Bodies and Sample Candidate Sites
-- Rules: Never invent scientific data. Mark placeholder data with is_placeholder.

-- 1. Celestial Bodies (Sourced from IAU / NASA planetary fact sheets)
INSERT INTO celestial_bodies (id, name, body_type, reference_system)
VALUES 
    ('mars', 'Mars', 'planet', 'IAU_MARS_2000'),
    ('moon', 'Moon', 'moon', 'MOON_ME_DE421')
ON CONFLICT (id) DO NOTHING;

-- 2. Candidate Landing Sites (Flagged with is_placeholder as required)
INSERT INTO candidate_landing_sites (id, name, body_id, coordinates, frame, analysis_radius_m, notes, is_placeholder)
VALUES 
    (
        'site-shackleton-01',
        'Shackleton Rim Candidate Area',
        'moon',
        '{"values": [-89.9, 0.0], "units": "deg", "frame": "MOON_ME_DE421"}'::jsonb,
        'MOON_ME_DE421',
        1000.0,
        'Placeholder candidate site for testing Backend B and Frontend integration.',
        true
    ),
    (
        'site-connecting-ridge-02',
        'Connecting Ridge Candidate Area',
        'moon',
        '{"values": [-89.5, 120.0], "units": "deg", "frame": "MOON_ME_DE421"}'::jsonb,
        'MOON_ME_DE421',
        1500.0,
        'Placeholder candidate site for testing terrain and illumination services.',
        true
    )
ON CONFLICT (id) DO NOTHING;
