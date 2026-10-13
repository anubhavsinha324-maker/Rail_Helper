"""
Real-world Corridor Dataset: Ghaziabad (GZB) to Aligarh (ALJN)
High-Density Network 1 (HDN-1), Northern / North Central Railway (106 km).
Equipped with Automatic Block Signaling (ABS) and multi-aspect signaling.
"""

from typing import List, Dict
from app.models.railway_network import (
    CorridorSection, Station, Track, TrackType, Direction, BlockSection, SignalingType, SpeedRestriction,
    RailwaySignal, SignalAspect, SignalType
)
from app.models.train import (
    Train, TrainCategory, TimetableEntry
)


def build_ghaziabad_aligarh_corridor() -> CorridorSection:
    """Build the physical 106 km GZB-ALJN corridor model."""
    stations = [
        Station(
            code="GZB",
            name="Ghaziabad Junction",
            km=0.0,
            is_junction=True,
            tracks=[
                Track(id="GZB_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="GZB_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="GZB_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=1),
                Track(id="GZB_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP, platform_number=2),
                Track(id="GZB_L3_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=3),
            ]
        ),
        Station(
            code="MIU",
            name="Maripat",
            km=13.0,
            is_junction=False,
            tracks=[
                Track(id="MIU_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="MIU_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="MIU_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN),
                Track(id="MIU_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP),
            ]
        ),
        Station(
            code="DER",
            name="Dadri (DFC Interchange)",
            km=22.0,
            is_junction=True,
            tracks=[
                Track(id="DER_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="DER_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="DER_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=1),
                Track(id="DER_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP, platform_number=2),
                Track(id="DER_CL_1", track_type=TrackType.COMMON_LOOP, direction=Direction.DOWN),
            ]
        ),
        Station(
            code="DKDE",
            name="Dankaur",
            km=32.0,
            is_junction=False,
            tracks=[
                Track(id="DKDE_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="DKDE_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="DKDE_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=1),
                Track(id="DKDE_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP, platform_number=2),
            ]
        ),
        Station(
            code="WAIR",
            name="Wair",
            km=51.0,
            is_junction=False,
            tracks=[
                Track(id="WAIR_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="WAIR_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="WAIR_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN),
                Track(id="WAIR_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP),
            ]
        ),
        Station(
            code="KRJ",
            name="Khurja Junction",
            km=65.0,
            is_junction=True,
            tracks=[
                Track(id="KRJ_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="KRJ_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="KRJ_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=1),
                Track(id="KRJ_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP, platform_number=2),
                Track(id="KRJ_L3_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=3),
            ]
        ),
        Station(
            code="SOM",
            name="Somna",
            km=86.0,
            is_junction=False,
            tracks=[
                Track(id="SOM_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="SOM_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="SOM_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN),
                Track(id="SOM_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP),
            ]
        ),
        Station(
            code="ALJN",
            name="Aligarh Junction",
            km=106.0,
            is_junction=True,
            tracks=[
                Track(id="ALJN_M_DN", track_type=TrackType.MAIN_LINE, direction=Direction.DOWN),
                Track(id="ALJN_M_UP", track_type=TrackType.MAIN_LINE, direction=Direction.UP),
                Track(id="ALJN_L1_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=1),
                Track(id="ALJN_L2_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP, platform_number=2),
                Track(id="ALJN_L3_DN", track_type=TrackType.LOOP_LINE, direction=Direction.DOWN, platform_number=3),
                Track(id="ALJN_L4_UP", track_type=TrackType.LOOP_LINE, direction=Direction.UP, platform_number=4),
            ]
        ),
    ]

    # Generate block sections between consecutive stations for both directions
    block_sections = []
    station_pairs = [
        ("GZB", "MIU", 13.0),
        ("MIU", "DER", 9.0),
        ("DER", "DKDE", 10.0),
        ("DKDE", "WAIR", 19.0),
        ("WAIR", "KRJ", 14.0),
        ("KRJ", "SOM", 21.0),
        ("SOM", "ALJN", 20.0),
    ]

    for from_st, to_st, dist in station_pairs:
        # DOWN direction (GZB -> ALJN)
        block_sections.append(BlockSection(
            id=f"BLK_DN_{from_st}_{to_st}",
            from_station_code=from_st,
            to_station_code=to_st,
            direction=Direction.DOWN,
            distance_km=dist,
            signaling=SignalingType.AUTOMATIC,
            sub_blocks=max(4, int(dist / 1.5)),
            safe_headway_sec=150,  # 2.5 minutes standard ABS headway
            section_mps_kmh=130.0
        ))
        # UP direction (ALJN -> GZB)
        block_sections.append(BlockSection(
            id=f"BLK_UP_{to_st}_{from_st}",
            from_station_code=to_st,
            to_station_code=from_st,
            direction=Direction.UP,
            distance_km=dist,
            signaling=SignalingType.AUTOMATIC,
            sub_blocks=max(4, int(dist / 1.5)),
            safe_headway_sec=150,
            section_mps_kmh=130.0
        ))

    # Realistic Permanent and Caution speed restrictions
    speed_restrictions = [
        SpeedRestriction(
            id="TSR-01",
            from_km=48.0,
            to_km=52.0,
            speed_limit_kmh=45.0,
            reason="Track Deep Screening & Ballast Tamping Work",
            is_temporary=True,
            active=False  # Can be activated by user in what-if simulation
        ),
        SpeedRestriction(
            id="PSR-01",
            from_km=64.0,
            to_km=66.0,
            speed_limit_kmh=75.0,
            reason="Khurja Yard Curve & Diamond Crossing",
            is_temporary=False,
            active=True
        )
    ]

    signals = _generate_signals_for_corridor(stations)

    return CorridorSection(
        name="Ghaziabad - Aligarh High Density Corridor (HDN-1)",
        description="106 km Quad/Double line trunk section with Automatic Block Signaling (ABS)",
        total_km=106.0,
        stations=stations,
        block_sections=block_sections,
        speed_restrictions=speed_restrictions,
        signals=signals
    )


def _generate_signals_for_corridor(stations: List[Station]) -> List[RailwaySignal]:
    """
    Generate Indian Railways signal network across the 106 km section:
    - Distance between each signal is 2.0 km.
    - Exactly 1 signal before each station (Home Signal at st.km - 1.0 for DOWN, st.km + 1.0 for UP).
    - Station Starter Signal at st.km.
    - Automatic Block Signals (ABS) spaced 2.0 km apart in block sections.
    """
    signals: List[RailwaySignal] = []
    st_map = {st.km: st for st in stations}
    st_kms = [st.km for st in stations]

    # 1. DOWN Direction (GZB 0 km -> ALJN 106 km)
    for i in range(len(st_kms)):
        curr_st_km = st_kms[i]
        curr_st = st_map[curr_st_km]
        
        # Starter signal at station
        signals.append(RailwaySignal(
            id=f"SIG_DN_STR_{curr_st.code}",
            name=f"{curr_st.code} Down Starter",
            km=curr_st_km,
            direction=Direction.DOWN,
            signal_type=SignalType.STARTER,
            current_aspect=SignalAspect.GREEN,
            station_code=curr_st.code
        ))

        if i < len(st_kms) - 1:
            next_st_km = st_kms[i + 1]
            next_st = st_map[next_st_km]
            
            # ABS signals spaced 2.0 km apart
            k = curr_st_km + 2.0
            while k < next_st_km - 1.5:
                signals.append(RailwaySignal(
                    id=f"ABS_DN_{int(k):03d}",
                    name=f"ABS-DN-{int(k):03d}",
                    km=k,
                    direction=Direction.DOWN,
                    signal_type=SignalType.AUTOMATIC,
                    current_aspect=SignalAspect.GREEN
                ))
                k += 2.0

            # Home signal 1 km before next station
            home_km = next_st_km - 1.0
            signals.append(RailwaySignal(
                id=f"SIG_DN_HOME_{next_st.code}",
                name=f"{next_st.code} Down Home",
                km=home_km,
                direction=Direction.DOWN,
                signal_type=SignalType.HOME,
                current_aspect=SignalAspect.GREEN,
                route_feather_active=False,
                station_code=next_st.code
            ))

    # 2. UP Direction (ALJN 106 km -> GZB 0 km)
    for i in range(len(st_kms) - 1, -1, -1):
        curr_st_km = st_kms[i]
        curr_st = st_map[curr_st_km]
        
        # Starter signal at station
        signals.append(RailwaySignal(
            id=f"SIG_UP_STR_{curr_st.code}",
            name=f"{curr_st.code} Up Starter",
            km=curr_st_km,
            direction=Direction.UP,
            signal_type=SignalType.STARTER,
            current_aspect=SignalAspect.GREEN,
            station_code=curr_st.code
        ))

        if i > 0:
            prev_st_km = st_kms[i - 1]
            prev_st = st_map[prev_st_km]
            
            # ABS signals spaced 2.0 km apart
            k = curr_st_km - 2.0
            while k > prev_st_km + 1.5:
                signals.append(RailwaySignal(
                    id=f"ABS_UP_{int(k):03d}",
                    name=f"ABS-UP-{int(k):03d}",
                    km=k,
                    direction=Direction.UP,
                    signal_type=SignalType.AUTOMATIC,
                    current_aspect=SignalAspect.GREEN
                ))
                k -= 2.0

            # Home signal 1 km before previous station in UP direction
            home_km = prev_st_km + 1.0
            signals.append(RailwaySignal(
                id=f"SIG_UP_HOME_{prev_st.code}",
                name=f"{prev_st.code} Up Home",
                km=home_km,
                direction=Direction.UP,
                signal_type=SignalType.HOME,
                current_aspect=SignalAspect.GREEN,
                route_feather_active=False,
                station_code=prev_st.code
            ))

    return signals


def time_to_sec(hh: int, mm: int, ss: int = 0) -> int:
    """Helper to convert HH:MM:SS to seconds from midnight."""
    return hh * 3600 + mm * 60 + ss


def get_default_train_traffic() -> List[Train]:
    """
    Generate realistic high-density train traffic for the section.
    Time window: 14:00:00 (50400s) to 16:30:00 (59400s).
    Includes Vande Bharat, Rajdhani, Express, MEMU commuter, and Freight trains.
    """
    trains: List[Train] = []

    # ----------------------------------------------------
    # DOWN TRAINS (GZB -> ALJN): Heading towards Kanpur / Prayagraj / Howrah
    # ----------------------------------------------------
    
    # 1. Slow Bulk Coal Freight (Enters section first at 14:00)
    # Without AI, this slow goods train will crawl on main line and delay the Vande Bharat & Rajdhani!
    trains.append(Train.create(
        id="TR_DN_BOXN_7041",
        number="BOXN/7041",
        name="Bulk Coal Freight (Dadri -> Harduaganj)",
        category=TrainCategory.BOXN_FREIGHT,
        direction="DOWN",
        schedule=[
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(14, 0), scheduled_departure_sec=time_to_sec(14, 2), min_dwell_sec=60),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(14, 16), scheduled_departure_sec=time_to_sec(14, 16)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(14, 26), scheduled_departure_sec=time_to_sec(14, 26)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(14, 38), scheduled_departure_sec=time_to_sec(14, 38)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(15, 2), scheduled_departure_sec=time_to_sec(15, 2)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(15, 18), scheduled_departure_sec=time_to_sec(15, 18)),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(15, 42), scheduled_departure_sec=time_to_sec(15, 42)),
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(16, 5), scheduled_departure_sec=time_to_sec(16, 10), min_dwell_sec=300),
        ],
        initial_delay_sec=0
    ))

    # 2. Delhi-Aligarh MEMU Local (All stops, leaves GZB at 14:08)
    trains.append(Train.create(
        id="TR_DN_MEMU_64102",
        number="64102",
        name="Delhi - Aligarh MEMU Passenger",
        category=TrainCategory.PASSENGER,
        direction="DOWN",
        schedule=[
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(14, 6), scheduled_departure_sec=time_to_sec(14, 8), is_commercial_stop=True),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(14, 20), scheduled_departure_sec=time_to_sec(14, 22), is_commercial_stop=True),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(14, 32), scheduled_departure_sec=time_to_sec(14, 34), is_commercial_stop=True),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(14, 45), scheduled_departure_sec=time_to_sec(14, 47), is_commercial_stop=True),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(15, 9), scheduled_departure_sec=time_to_sec(15, 11), is_commercial_stop=True),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(15, 26), scheduled_departure_sec=time_to_sec(15, 28), is_commercial_stop=True),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(15, 50), scheduled_departure_sec=time_to_sec(15, 52), is_commercial_stop=True),
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(16, 14), scheduled_departure_sec=time_to_sec(16, 20), is_commercial_stop=True),
        ],
        initial_delay_sec=0
    ))

    # 3. Superfast Express (12418 Prayagraj Express, passes GZB at 14:18)
    trains.append(Train.create(
        id="TR_DN_SF_12418",
        number="12418",
        name="Prayagraj Express",
        category=TrainCategory.SUPERFAST,
        direction="DOWN",
        schedule=[
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(14, 16), scheduled_departure_sec=time_to_sec(14, 18), is_commercial_stop=False),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(14, 26), scheduled_departure_sec=time_to_sec(14, 26)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(14, 32), scheduled_departure_sec=time_to_sec(14, 32)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(14, 38), scheduled_departure_sec=time_to_sec(14, 38)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(14, 50), scheduled_departure_sec=time_to_sec(14, 50)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(14, 59), scheduled_departure_sec=time_to_sec(14, 59)),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(15, 12), scheduled_departure_sec=time_to_sec(15, 12)),
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(15, 25), scheduled_departure_sec=time_to_sec(15, 27), is_commercial_stop=True),
        ],
        initial_delay_sec=0
    ))

    # 4. Premium Flagship: Vande Bharat Express (22436 New Delhi - Varanasi)
    # Passes GZB at 14:28 at 130 km/h. High priority! Needs uninterrupted green wave!
    trains.append(Train.create(
        id="TR_DN_VB_22436",
        number="22436",
        name="Vande Bharat Express (NDLS -> BSB)",
        category=TrainCategory.VANDE_BHARAT,
        direction="DOWN",
        schedule=[
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(14, 26), scheduled_departure_sec=time_to_sec(14, 28), is_commercial_stop=False),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(14, 35), scheduled_departure_sec=time_to_sec(14, 35)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(14, 40), scheduled_departure_sec=time_to_sec(14, 40)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(14, 45), scheduled_departure_sec=time_to_sec(14, 45)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(14, 55), scheduled_departure_sec=time_to_sec(14, 55)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(15, 2), scheduled_departure_sec=time_to_sec(15, 2)),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(15, 13), scheduled_departure_sec=time_to_sec(15, 13)),
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(15, 23), scheduled_departure_sec=time_to_sec(15, 25), is_commercial_stop=True),
        ],
        initial_delay_sec=0
    ))

    # 5. Howrah Rajdhani Express (12302)
    # Departs GZB close behind Vande Bharat at 14:38 at 130 km/h
    trains.append(Train.create(
        id="TR_DN_RAJ_12302",
        number="12302",
        name="Howrah Rajdhani Express",
        category=TrainCategory.RAJDHANI,
        direction="DOWN",
        schedule=[
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(14, 36), scheduled_departure_sec=time_to_sec(14, 38), is_commercial_stop=False),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(14, 45), scheduled_departure_sec=time_to_sec(14, 45)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(14, 50), scheduled_departure_sec=time_to_sec(14, 50)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(14, 55), scheduled_departure_sec=time_to_sec(14, 55)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(15, 5), scheduled_departure_sec=time_to_sec(15, 5)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(15, 12), scheduled_departure_sec=time_to_sec(15, 12)),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(15, 23), scheduled_departure_sec=time_to_sec(15, 23)),
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(15, 34), scheduled_departure_sec=time_to_sec(15, 36), is_commercial_stop=False),
        ],
        initial_delay_sec=0
    ))

    # 6. High-Priority Container Freight (CONCOR)
    trains.append(Train.create(
        id="TR_DN_CONCOR_884",
        number="CONCOR/884",
        name="Dadri Port Container Rake",
        category=TrainCategory.CONCOR_CONTAINER,
        direction="DOWN",
        schedule=[
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(14, 50), scheduled_departure_sec=time_to_sec(14, 52)),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(15, 3), scheduled_departure_sec=time_to_sec(15, 3)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(15, 12), scheduled_departure_sec=time_to_sec(15, 12)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(15, 21), scheduled_departure_sec=time_to_sec(15, 21)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(15, 41), scheduled_departure_sec=time_to_sec(15, 41)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(15, 55), scheduled_departure_sec=time_to_sec(15, 55)),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(16, 15), scheduled_departure_sec=time_to_sec(16, 15)),
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(16, 35), scheduled_departure_sec=time_to_sec(16, 40)),
        ],
        initial_delay_sec=0
    ))

    # ----------------------------------------------------
    # UP TRAINS (ALJN -> GZB): Heading towards New Delhi
    # ----------------------------------------------------
    
    # 7. Vande Bharat Express UP (22435 Varanasi -> New Delhi)
    trains.append(Train.create(
        id="TR_UP_VB_22435",
        number="22435",
        name="Vande Bharat Express (BSB -> NDLS)",
        category=TrainCategory.VANDE_BHARAT,
        direction="UP",
        schedule=[
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(14, 15), scheduled_departure_sec=time_to_sec(14, 17), is_commercial_stop=True),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(14, 27), scheduled_departure_sec=time_to_sec(14, 27)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(14, 38), scheduled_departure_sec=time_to_sec(14, 38)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(14, 46), scheduled_departure_sec=time_to_sec(14, 46)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(14, 56), scheduled_departure_sec=time_to_sec(14, 56)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(15, 2), scheduled_departure_sec=time_to_sec(15, 2)),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(15, 7), scheduled_departure_sec=time_to_sec(15, 7)),
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(15, 15), scheduled_departure_sec=time_to_sec(15, 17), is_commercial_stop=False),
        ],
        initial_delay_sec=0
    ))

    # 8. Dibrugarh Rajdhani Express UP (12423)
    trains.append(Train.create(
        id="TR_UP_RAJ_12423",
        number="12423",
        name="Dibrugarh Rajdhani Express",
        category=TrainCategory.RAJDHANI,
        direction="UP",
        schedule=[
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(14, 28), scheduled_departure_sec=time_to_sec(14, 30), is_commercial_stop=False),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(14, 41), scheduled_departure_sec=time_to_sec(14, 41)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(14, 52), scheduled_departure_sec=time_to_sec(14, 52)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(15, 0), scheduled_departure_sec=time_to_sec(15, 0)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(15, 10), scheduled_departure_sec=time_to_sec(15, 10)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(15, 16), scheduled_departure_sec=time_to_sec(15, 16)),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(15, 21), scheduled_departure_sec=time_to_sec(15, 21)),
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(15, 30), scheduled_departure_sec=time_to_sec(15, 32), is_commercial_stop=False),
        ],
        initial_delay_sec=0
    ))

    # 9. Empty Coal Rake Freight UP
    trains.append(Train.create(
        id="TR_UP_BOXN_9912",
        number="BOXN/9912",
        name="Empty Coal Rake (Harduaganj -> Chandausi)",
        category=TrainCategory.BOXN_FREIGHT,
        direction="UP",
        schedule=[
            TimetableEntry(station_code="ALJN", scheduled_arrival_sec=time_to_sec(14, 2), scheduled_departure_sec=time_to_sec(14, 5)),
            TimetableEntry(station_code="SOM", scheduled_arrival_sec=time_to_sec(14, 28), scheduled_departure_sec=time_to_sec(14, 28)),
            TimetableEntry(station_code="KRJ", scheduled_arrival_sec=time_to_sec(14, 52), scheduled_departure_sec=time_to_sec(14, 52)),
            TimetableEntry(station_code="WAIR", scheduled_arrival_sec=time_to_sec(15, 10), scheduled_departure_sec=time_to_sec(15, 10)),
            TimetableEntry(station_code="DKDE", scheduled_arrival_sec=time_to_sec(15, 32), scheduled_departure_sec=time_to_sec(15, 32)),
            TimetableEntry(station_code="DER", scheduled_arrival_sec=time_to_sec(15, 45), scheduled_departure_sec=time_to_sec(15, 45)),
            TimetableEntry(station_code="MIU", scheduled_arrival_sec=time_to_sec(15, 57), scheduled_departure_sec=time_to_sec(15, 57)),
            TimetableEntry(station_code="GZB", scheduled_arrival_sec=time_to_sec(16, 12), scheduled_departure_sec=time_to_sec(16, 15)),
        ],
        initial_delay_sec=0
    ))

    return trains
