import logging
import numpy as np
import bottleneck as bn

def frame_phase_velocity(phases):
    try:
        tmp1 = phases[:-1]
        tmp2 = phases[1:]
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
        return bn.move_mean( velocity, window=5, min_count=1 )
    except Exception as e:
        print(f'Exception: phase velocity: {e}')
        # dont die but create a noticable result
        return phases

def frame_unroll_phases(phases):
    try:
        count = 0
        unroll = np.copy(phases)
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
        return unroll,count
    except Exception as e:
        print(f'Exception: unroll_phases: {e}')
        # dont die but create a noticable result
        return phases,0

# return a (4) array of R,G,B, A values
def frame_rgba(readings,idx,magnitudes,phases,phases_unrolled,phase_velocity,rollover_count):
    rgba = readings.rgba[:,idx]
    if rgba[1,3] == 0:
        # don't repeat the work
        rgba[1:2,3] = 255
        #rgba[0,idx,0] = int( np.mean(magnitudes) / 3)
        #rgba[0,idx,0] = 0
        rgba[1,2] = 0
        if rollover_count >= 0:
            rgba[1,1] = 255 - rollover_count * 25
            rgba[1,0] = 255
        else:
            rgba[1,1] = 255
            rgba[1,0] = 255 + rollover_count * 25
        np.clip(rgba[1],0, 255)

        mag = 255 - int( np.mean(magnitudes) / 3)
        if mag < 0:
            mag = 0
        rgba[2,0:2] = mag
        # marker
        rgba[0,0:2] = 0
        rgba[0,3] = 255

# if idx < window_s
def calc_window(idx,window_size,readings):
    
    if idx < window_size:
        return 0,window_size

    idx_min = int(idx - window_size / 2)
    idx_max = int(idx + window_size / 2)

    if idx_max >= readings.head:
        return readings.head - window_size,readings.head + 1

    return idx_min,idx_max


# def foo:
#         im_data[i] = im_data[i+1]
#     im_data[bin_count - 1] = fft_final

#     im.set_array(im_data.transpose())