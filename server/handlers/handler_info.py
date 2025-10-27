#!/usr/bin/env python3


class HandlerInfo(object):
    def __init__(self, *args, **kwargs) -> None:
        self.subprograms = {}

    def set_subprogram(self, program_id, sub_t):
        print(f"[HANDLER-INFO-SET] set_subprogram called for {program_id}")
        print(f"[HANDLER-INFO-SET] New thread: {sub_t}")
        print(f"[HANDLER-INFO-SET] Existing subprograms before: {list(self.subprograms.keys())}")

        # Stop existing if any
        self.stop_subprogram(program_id)

        # Set new subprogram
        self.subprograms[program_id] = sub_t
        print(f"[HANDLER-INFO-SET] Subprogram {program_id} registered")
        print(f"[HANDLER-INFO-SET] Existing subprograms after: {list(self.subprograms.keys())}")

    def get_subprogram(self, program_id):
        """Get a running subprogram by ID"""
        return self.subprograms.get(program_id, None)

    def remove_subprogram(self, program_id):
        if program_id is None:
            self.stop_subprogram()
            self.subprograms.clear()
        elif program_id in self.subprograms:
            self.stop_subprogram(program_id)
            self.subprograms.pop(program_id, None)

    def start_subprogram(self, program_id):
        print(f"[HANDLER-INFO-START] start_subprogram called for {program_id}")
        if program_id in self.subprograms:
            thread = self.subprograms[program_id]
            print(f"[HANDLER-INFO-START] Found thread: {thread}")
            print(f"[HANDLER-INFO-START] Thread alive before start: {thread.is_alive() if hasattr(thread, 'is_alive') else 'N/A'}")
            thread.start()
            print(f"[HANDLER-INFO-START] Thread started for {program_id}")
        else:
            print(f"[HANDLER-INFO-START] ERROR: program_id {program_id} not found in subprograms")

    def stop_subprogram(self, program_id):
        print(f"[HANDLER-INFO-STOP] stop_subprogram called with program_id: {program_id}")
        print(f"[HANDLER-INFO-STOP] Current subprograms: {list(self.subprograms.keys())}")

        if program_id is None:
            # Stop all subprograms
            print(f"[HANDLER-INFO-STOP] Stopping all {len(self.subprograms)} subprograms")
            # Make a copy to avoid modifying dict during iteration
            subprograms_copy = list(self.subprograms.items())

            # Stop all threads
            for pid, t in subprograms_copy:
                print(f"[HANDLER-INFO-STOP] Stopping {pid}: {t}")
                try:
                    t.stop()
                except Exception as e:
                    print(f"[HANDLER-INFO-STOP] Error stopping {pid}: {e}")

            # Join all threads and clear the dictionary
            for pid, t in subprograms_copy:
                try:
                    print(f"[HANDLER-INFO-STOP] Joining thread {pid}")
                    t.join(timeout=0.5)  # Wait max 0.5 seconds per thread
                except Exception as e:
                    print(f"[HANDLER-INFO-STOP] Error joining {pid}: {e}")

            # Clear all subprograms after stopping
            self.subprograms.clear()
            print(f"[HANDLER-INFO-STOP] Cleared all subprograms")
        elif program_id in self.subprograms:
            try:
                t = self.subprograms.pop(program_id)
                print(f"[HANDLER-INFO-STOP] Found and popped subprogram {program_id}: {t}")
                print(f"[HANDLER-INFO-STOP] Thread alive before stop: {t.is_alive() if hasattr(t, 'is_alive') else 'N/A'}")

                t.stop()
                print(f"[HANDLER-INFO-STOP] stop() called on {program_id}")

                t.join(timeout=0.5)  # Wait max 0.5 seconds for thread to finish
                print(f"[HANDLER-INFO-STOP] Thread alive after join: {t.is_alive() if hasattr(t, 'is_alive') else 'N/A'}")
                print(f"[HANDLER-INFO-STOP] Subprogram {program_id} stopped and joined")
            except Exception as e:
                print(f"[HANDLER-INFO-STOP] Error stopping subprogram {program_id}: {e}")
                import traceback
                traceback.print_exc()
                pass
        else:
            print(f"[HANDLER-INFO-STOP] Program ID {program_id} not found in subprograms")
