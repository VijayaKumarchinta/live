INSERT INTO config.line (line_id, name, site, timezone)
VALUES (30, 'Line Speed 30', 'Plant A', 'Asia/Kolkata')
ON CONFLICT (line_id) DO NOTHING;

INSERT INTO config.sensor (sensor_id, line_id, tag, display_name, unit, zero_is_missing)
VALUES
    (1, 30, 'line_speed',       'Line Speed',        'm/min', FALSE),
    (2, 30, 'oil_temperature',  'Oil Temperature',   'C',     FALSE),
    (3, 30, 'paddle_speed',     'Paddle Speed',      'rpm',   FALSE),
    (4, 30, 'motor_current',    'Motor Current',     'A',     FALSE),
    (5, 30, 'vibration',        'Vibration',         'mm/s',  FALSE)
ON CONFLICT (sensor_id) DO NOTHING;
