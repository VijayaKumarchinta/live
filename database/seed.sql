INSERT INTO config.line (line_id, name, site, timezone)
VALUES (30, 'Line Speed 30', 'Plant A', 'Asia/Kolkata')
ON CONFLICT (line_id) DO NOTHING;

INSERT INTO config.sensor (sensor_id, line_id, tag, display_name, unit, zero_is_missing)
VALUES
    (1,  30, 'Burner Output Load',                                   'Burner Output Load',       '',   FALSE),
    (2,  30, 'Burner PV',                                            'Burner PV',                '',   FALSE),
    (3,  30, 'Burner SP',                                            'Burner SP',                '',   FALSE),
    (4,  30, '{[PLC1]Input.Analogue.AT6802.O_Filtered}',             'PLC1 AT6802 Filtered',     '',   FALSE),
    (5,  30, 'oil Level PV',                                         'Oil Level PV',             '',   FALSE),
    (6,  30, '{[PLC1]Input.Analogue.TT4401.O_Filtered}',             'PLC1 TT4401 Filtered',     '',   TRUE),
    (7,  30, '{[PLC1]Input.Analogue.TT5101.O_Filtered}',             'PLC1 TT5101 Filtered',     '',   FALSE),
    (8,  30, 'Air Inlet To Burner',                                  'Air Inlet To Burner',      '',   FALSE),
    (9,  30, 'Heat Exchanger Stack Temp',                            'Stack Temp',               'C',  FALSE),
    (10, 30, 'APH Outlet',                                           'APH Outlet',               '',   FALSE),
    (11, 30, 'Ambient Air Temp',                                     'Ambient Air Temp',         'C',  FALSE),
    (12, 30, 'Oil Inlet Temperature',                                'Oil Inlet Temperature',    'C',  FALSE),
    (13, 30, '{[PLC1]Input.Analogue.TT6102.O_Filtered}',             'PLC1 TT6102 Filtered',     '',   FALSE),
    (14, 30, '{[PLC1]Input.Analogue.TT7101.O_Filtered}',             'PLC1 TT7101 Filtered',     '',   FALSE),
    (15, 30, '{[PLC1]Input.Analogue.TT7102.O_Filtered}',             'PLC1 TT7102 Filtered',     '',   FALSE),
    (16, 30, '{[PLC1]Input.Analogue.TT7103.O_Filtered}',             'PLC1 TT7103 Filtered',     '',   FALSE),
    (17, 30, 'Pump Loading',                                         'Pump Loading',             '',   FALSE),
    (18, 30, 'Pump Load PV',                                         'Pump Load PV',             '',   FALSE),
    (19, 30, 'Pump load SP',                                         'Pump Load SP',             '',   FALSE),
    (20, 30, '{[PLC1]MoistureControl.I_MoistureHighSetpoint1}',      'Moisture High SP1',        '',   FALSE),
    (21, 30, '{[PLC1]MoistureControl.I_MoistureHighSetpoint2}',      'Moisture High SP2',        '',   FALSE),
    (22, 30, '{[PLC1]MoistureControl.I_MoistureLowSetpoint1}',       'Moisture Low SP1',         '',   FALSE),
    (23, 30, '{[PLC1]MoistureControl.I_MoistureLowSetpoint2}',       'Moisture Low SP2',         '',   FALSE),
    (24, 30, '{[PLC1]MoistureControl.O_SpeedPIDCV}',                 'Speed PID CV',             '',   FALSE),
    (25, 30, 'Moisture PV',                                          'Moisture PV',              '',   FALSE),
    (26, 30, '{[PLC1]MoistureControl.O_SpeedPIDSP}',                 'Speed PID SP',             '',   FALSE),
    (27, 30, '{[PLC1]MoistureControl.O_TempPIDCV}',                  'Temp PID CV',              '',   FALSE),
    (28, 30, '{[PLC1]MoistureControl.O_TempPIDPV}',                  'Temp PID PV',              '',   FALSE),
    (29, 30, '{[PLC1]MoistureControl.O_TempPIDSP}',                  'Temp PID SP',              '',   FALSE),
    (30, 30, 'Paddle Speed',                                         'Paddle Speed',             'rpm', FALSE),
    (31, 30, '{[PLC1]Valve.XV6601.OM_Open}',                         'Valve XV6601 Open',        '',   FALSE),
    (32, 30, 'DeltaT',                                               'Delta T',                  '',   FALSE)
ON CONFLICT (sensor_id) DO NOTHING;