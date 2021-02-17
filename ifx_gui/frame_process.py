import logging
import numpy as np
import bottleneck as bn

# this is the entry point
def process_frame(readings, idx, reading):

    reading.packet = reading["data_i"] + reading["data_q"] * 1j
    reading.magnitudes = np.absolute(reading.packet)
    reading.phases = np.angle(reading.packet)
    frame_unroll_phases(reading)
    frame_phase_velocity(reading)
    frame_rgba(readings, idx, reading)

def frame_phase_velocity(reading):
    try:
        tmp1 = reading.phases[:-1]
        tmp2 = reading.phases[1:]
        velocity = np.subtract(tmp2,tmp1)
        pi_2 = np.pi / 2
        #velocity = np.subtract(phases[:-1], phases[1:])
        with np.nditer(velocity, op_flags=['readwrite']) as it:
            for v in it:
                if v < -pi_2:
                    tmp = v + np.pi
                    while tmp < -pi_2:
                        tmp += np.pi
                    v[...] = tmp
                elif v > pi_2:
                    tmp = v - np.pi
                    while tmp > pi_2:
                        tmp -= np.pi
                    v[...] = tmp
        #reading.phase_velocity = bn.move_mean( velocity, window=5, min_count=1 )
        reading.phase_velocity = velocity
    except Exception as e:
        print(f'Exception: phase velocity: {e}')
        # dont die but create a noticable result
        reading.phase_velocity = reading.phases

def frame_unroll_phases(reading):
    try:
        count = 0
        unroll = np.copy(reading.phases)
        offset = 0
        last_v = 0
        threshold = np.pi * 0.8
        for i in range(len(unroll)):
            v = unroll[i]
            if v > threshold and last_v < -threshold:
                # negative rollover
                offset -= np.pi * 2
                count -= 1
            elif v < -threshold and last_v > threshold:
                # negative rollover
                offset += np.pi * 2
                count += 1
            last_v = v
            unroll[i] = v + offset
        reading.phases_unrolled = unroll
        reading.rollover_count = count
    except Exception as e:
        print(f'Exception: unroll_phases: {e}')
        # dont die but create a noticable result
        reading.phases_unrolled = reading.phases
        reading.rollover_count = 0

def clip(i):
    if i < 0: return 0
    if i > 255: return 255
    return i

# return a (4) array of R,G,B, A values
def frame_rgba(readings,idx, reading):
    rgba = readings.rgba[:,idx]
    if rgba[1,3] == 0:
        # dont repeat the work
        rgba[1:2,3] = 255
        rgba[1,2] = 0
        if reading.rollover_count >= 0:
            rgba[1,1] = clip( 255 - reading.rollover_count * 25 )
            rgba[1,0] = 255
        else:
            rgba[1,1] = 255
            rgba[1,0] = clip( 255 + reading.rollover_count * 25 )

        mag = clip( 255 - int( np.mean(reading.magnitudes) / 3))
        rgba[2,0:2] = mag
        # marker
        rgba[0,0:2] = 0
        rgba[0,0:0] = 0
