import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Global parameters
baud_rate = 115200  # bits per second
bits_per_byte = 10  # 8 data bits + start + stop
total_time = 1    # total simulation time in seconds

# Define our messages as a list of dicts.
# Each message has an ID, message_size_bytes, and frequency (Hz).
messages = [
    {"id": "M1", "message_size_bytes": 4,  "frequency": 890},
    {"id": "M2", "message_size_bytes": 10, "frequency": 31},
    {"id": "M3", "message_size_bytes": 33, "frequency": 2},
    # you can add more messages here...
]

def message_duration(message_size_bytes, baud_rate):
    """Compute duration of a full (un-chunked) message in seconds."""
    message_size_bits = message_size_bytes * bits_per_byte
    return message_size_bits / baud_rate

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

def schedule_messages(messages, total_time, baud_rate):
    """
    Schedule transmissions for messages on a common timeline so that no two transmissions overlap.
    
    Priority: messages with higher frequency (faster messages) are scheduled first.
    Lower priority (slower) messages are split (chunked) into pieces that fill the gaps left.
    
    Returns:
      schedule: list of scheduled intervals as tuples:
         (start_time, end_time, message_id, instance_index)
    """
    # Calculate each message's duration and period; add these to each dict.
    for m in messages:
        m["duration"] = message_duration(m["message_size_bytes"], baud_rate)
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
        duration = m["duration"]
        instance_index = 0  # which occurrence of the message we are scheduling
        
        # Schedule all instances that occur within the simulation time.
        t_instance = 0
        while t_instance < total_time:
            period_start = t_instance
            period_end = min(t_instance + period, total_time)
            
            remaining = duration  # how much time we need to schedule in this period
            # Get free intervals in [period_start, period_end]
            free_intervals = get_free_intervals(busy_intervals, period_start, period_end)
            
            # For each free interval, schedule as much as possible.
            for free_start, free_end in free_intervals:
                gap = free_end - free_start
                if gap <= 0:
                    continue
                chunk = min(remaining, gap)
                chunk_start = free_start
                chunk_end = free_start + chunk
                # Create the scheduled chunk
                scheduled_chunk = (chunk_start, chunk_end, msg_id, instance_index)
                schedule.append(scheduled_chunk)
                add_interval(busy_intervals, scheduled_chunk)
                
                remaining -= chunk
                if remaining <= 1e-12:  # scheduled enough (allowing for floating-point tolerance)
                    break
            if remaining > 1e-12:
                print(f"WARNING: Could not fully schedule message {msg_id} instance {instance_index}. "
                      f"Missing {remaining:.6f}s transmission time in period starting at {period_start:.6f}s")
            
            instance_index += 1
            t_instance += period

    # Sort the final schedule by start time for clarity.
    schedule.sort(key=lambda x: x[0])
    return schedule

def plot_schedule(schedule, total_time):
    """
    Plot the schedule as horizontal bars on a timeline.
    Each message gets its own color.
    """
    # Get unique message ids
    msg_ids = sorted(list(set(chunk[2] for chunk in schedule)))
    cmap = cm.get_cmap('tab10', len(msg_ids))
    color_map = {msg_id: cmap(i) for i, msg_id in enumerate(msg_ids)}
    
    plt.figure(figsize=(12, 6))
    for chunk in schedule:
        start, end, msg_id, instance = chunk
        plt.hlines(msg_id, start, end, colors=color_map[msg_id], lw=6,
                   label=msg_id if instance == 0 else "")  # only add label once

    plt.xlabel("Time (s)")
    plt.title("Scheduled Message Transmissions (Chunked)")
    plt.xlim(0, total_time)
    plt.yticks(msg_ids)
    plt.grid(True)
    plt.legend()
    plt.show()

# Run the scheduling algorithm
schedule = schedule_messages(messages, total_time, baud_rate)

# Print out the scheduled intervals for reference
print("Scheduled Transmission Chunks:")
for chunk in schedule:
    start, end, msg_id, instance = chunk
    print(f"Message {msg_id} (instance {instance}): {start:.6f}s -> {end:.6f}s, duration: {end-start:.6f}s")

# Plot the schedule
plot_schedule(schedule, total_time)
