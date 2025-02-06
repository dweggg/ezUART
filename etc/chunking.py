import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import math

# Global parameters
baud_rate = 115200       # bits per second
bits_per_byte = 10       # 8 data bits + start + stop bits
total_time = 1           # total simulation time in seconds

# Overhead for each chunk (in bytes)
overhead_bytes = 2       # For example, 2 bytes of overhead per transmitted chunk
min_payload_multiple = 4 # Each chunk's payload must be a multiple of 4 bytes

# Define our messages as a list of dicts.
# Each message has an ID, message_size_bytes (payload only), and frequency (Hz).
messages = [
    {"id": "M1", "message_size_bytes": 4,  "frequency": 500},
    {"id": "M2", "message_size_bytes": 50, "frequency": 31},
    {"id": "M3", "message_size_bytes": 100, "frequency": 2},
    # You can add more messages here...
]

def get_free_intervals(busy_intervals, period_start, period_end):
    """
    Given a sorted list of busy intervals and a time window [period_start, period_end],
    return a list of free intervals (as (start, end)) within that window.
    Assumes busy_intervals are non-overlapping.
    """
    free_intervals = []
    current = period_start

    # Consider only busy intervals that intersect the period
    for interval in busy_intervals:
        busy_start, busy_end, msg_id, instance_index = interval  # Unpack the full interval
        # Skip intervals that end before the period starts
        if busy_end <= period_start:
            continue
        # If busy interval starts after the current free time, we have a gap.
        if busy_start > current:
            free_intervals.append((current, min(busy_start, period_end)))
        # Advance current to after the busy interval.
        current = max(current, busy_end)
        if current >= period_end:
            break
    # If there's free time at the end
    if current < period_end:
        free_intervals.append((current, period_end))
    return free_intervals

def add_interval(busy_intervals, new_interval):
    """
    Insert new_interval = (start, end, message_id, instance_index)
    into the busy_intervals list and keep it sorted.
    """
    busy_intervals.append(new_interval)
    busy_intervals.sort(key=lambda x: x[0])

def schedule_messages(messages, total_time, baud_rate, overhead_bytes, min_payload_multiple=4):
    """
    Schedule transmissions for messages on a common timeline so that no two transmissions overlap.
    
    Each message instance has a payload (message_size_bytes) that must be sent within its period.
    If the payload cannot be transmitted in one contiguous block, it is split into chunks.
    Each chunk carries an overhead (overhead_bytes) and the chunk's payload must be a multiple
    of min_payload_multiple bytes.
    
    Priority: messages with higher frequency (faster messages) are scheduled first.
    Lower priority (slower) messages are chunked into pieces that fill in the gaps.
    
    Returns:
      schedule: list of scheduled intervals as tuples:
         (start_time, end_time, message_id, instance_index, payload_bytes_sent)
    """
    # For each message, compute its period (seconds)
    for m in messages:
        m["period"] = 1 / m["frequency"]
    
    # Sort messages by frequency descending (highest frequency = smallest period first)
    messages_sorted = sorted(messages, key=lambda m: m["frequency"], reverse=True)
    
    # Our timeline of busy intervals (each: (start, end, message_id, instance_index))
    busy_intervals = []
    schedule = []  # record scheduled chunks
    
    # For each message (in order of descending priority)
    for m in messages_sorted:
        msg_id = m["id"]
        period = m["period"]
        total_payload = m["message_size_bytes"]  # payload bytes per instance
        instance_index = 0  # which occurrence of the message we are scheduling
        
        # Schedule all instances that occur within the simulation time.
        t_instance = 0
        while t_instance < total_time:
            period_start = t_instance
            period_end = min(t_instance + period, total_time)
            
            remaining_payload = total_payload  # payload bytes still to send in this period
            
            # Get free intervals in [period_start, period_end]
            free_intervals = get_free_intervals(busy_intervals, period_start, period_end)
            
            # For each free interval, try to send as much of the remaining payload as possible.
            for free_start, free_end in free_intervals:
                gap_time = free_end - free_start
                # Calculate available capacity (in bytes) in this gap.
                # Each byte takes (bits_per_byte / baud_rate) seconds.
                available_bytes = math.floor(gap_time * baud_rate / bits_per_byte)
                
                # We must leave room for overhead in each chunk.
                if available_bytes <= overhead_bytes:
                    continue  # not enough space to even send overhead + minimal payload
                
                # Maximum payload bytes we can send in this gap
                max_payload_in_gap = available_bytes - overhead_bytes
                
                # We cannot send more than what remains.
                desired_payload = min(remaining_payload, max_payload_in_gap)
                # Adjust desired_payload downward so that it is a multiple of min_payload_multiple.
                desired_payload = desired_payload - (desired_payload % min_payload_multiple)
                
                # If desired_payload is 0, we might not be able to send any chunk in this gap.
                if desired_payload <= 0:
                    continue
                
                # Calculate the total bytes to send in this chunk (payload + overhead)
                chunk_bytes = desired_payload + overhead_bytes
                # Compute the transmission time for this chunk.
                chunk_time = chunk_bytes * bits_per_byte / baud_rate
                
                # Check that the chunk fits in the current free interval (it should, by construction).
                if free_start + chunk_time > free_end + 1e-12:
                    # If not, reduce desired_payload further until it fits.
                    # (This is a fallback; ideally our math should have ensured it fits.)
                    while free_start + chunk_time > free_end and desired_payload >= min_payload_multiple:
                        desired_payload -= min_payload_multiple
                        chunk_bytes = desired_payload + overhead_bytes
                        chunk_time = chunk_bytes * bits_per_byte / baud_rate
                    if desired_payload < min_payload_multiple:
                        continue
                
                # Schedule the chunk.
                chunk_start = free_start
                chunk_end = free_start + chunk_time
                scheduled_chunk = (chunk_start, chunk_end, msg_id, instance_index, desired_payload)
                schedule.append(scheduled_chunk)
                add_interval(busy_intervals, scheduled_chunk[:4])  # only time info, id and instance are used for conflicts
                
                # Update remaining payload.
                remaining_payload -= desired_payload
                
                # If there is still room in the free interval, update free_start for the next chunk in the same gap.
                # (In our simple approach, we assume the whole free interval is used chunk‐by‐chunk.)
                # In a more advanced version, you might split the free interval and continue.
                # Here, we simply move on after scheduling one chunk per free interval.
                # Alternatively, if there is still time, we could try to use the remaining part of this free interval:
                # free_start = chunk_end
                # But note that the free_intervals list is fixed for this period.
                
                if remaining_payload <= 0:
                    break  # finished scheduling this instance
            if remaining_payload > 0:
                print(f"WARNING: Could not fully schedule message {msg_id} instance {instance_index}. "
                      f"Missing {remaining_payload} payload bytes in period starting at {period_start:.6f}s")
            
            instance_index += 1
            t_instance += period

    # Sort the final schedule by start time for clarity.
    schedule.sort(key=lambda x: x[0])
    return schedule

def plot_schedule(schedule, total_time):
    """
    Plot the schedule as horizontal bars on a timeline.
    Each message gets its own color.
    
    The plot shows the time intervals for each chunk and indicates the payload bytes sent.
    """
    # Get unique message ids
    msg_ids = sorted(list(set(chunk[2] for chunk in schedule)))
    cmap = cm.get_cmap('tab10', len(msg_ids))
    color_map = {msg_id: cmap(i) for i, msg_id in enumerate(msg_ids)}
    
    plt.figure(figsize=(12, 6))
    for chunk in schedule:
        start, end, msg_id, instance, payload = chunk
        plt.hlines(msg_id, start, end, colors=color_map[msg_id], lw=6,
                   label=msg_id if instance == 0 else "")
        # Optionally, annotate the chunk with the payload sent:
        plt.text((start+end)/2, 0.95 + msg_ids.index(msg_id), f"{payload}B",
                 horizontalalignment='center', verticalalignment='center', color="white", fontsize=8)
        
    plt.xlabel("Time (s)")
    plt.title("Scheduled Message Transmissions (Chunked with Overhead)")
    plt.xlim(0, total_time)
    plt.yticks(range(len(msg_ids)), msg_ids)
    plt.grid(True)
    plt.legend()
    plt.show()

# Run the scheduling algorithm with the overhead and payload constraints
schedule = schedule_messages(messages, total_time, baud_rate, overhead_bytes, min_payload_multiple)

# Print out the scheduled intervals for reference
print("Scheduled Transmission Chunks:")
for chunk in schedule:
    start, end, msg_id, instance, payload = chunk
    total_bytes = payload + overhead_bytes
    print(f"Message {msg_id} (instance {instance}): {start:.6f}s -> {end:.6f}s, "
          f"payload: {payload}B, total bytes (with overhead): {total_bytes}B, "
          f"duration: {end-start:.6f}s")

# Plot the schedule
plot_schedule(schedule, total_time)
