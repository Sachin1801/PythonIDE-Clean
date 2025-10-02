#!/usr/bin/env python3


class HandlerInfo(object):
    def __init__(self, *args, **kwargs) -> None:
        self.subprograms = {}

    def set_subprogram(self, program_id, sub_t):
        self.stop_subprogram(program_id)
        self.subprograms[program_id] = sub_t

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
        if program_id in self.subprograms:
            self.subprograms[program_id].start()

    def stop_subprogram(self, program_id):
        if program_id is None:
            # Stop all subprograms
            for _, t in self.subprograms.items():
                t.stop()
            # Join all threads to ensure complete shutdown
            for _, t in self.subprograms.items():
                try:
                    t.join(timeout=0.5)  # Wait max 0.5 seconds per thread
                except:
                    pass
        elif program_id in self.subprograms:
            try:
                t = self.subprograms.pop(program_id)
                print(f"[HANDLER-INFO] Stopping subprogram {program_id}")
                t.stop()
                t.join(timeout=0.5)  # Wait max 0.5 seconds for thread to finish
                print(f"[HANDLER-INFO] Subprogram {program_id} stopped and joined")
            except Exception as e:
                print(f"[HANDLER-INFO] Error stopping subprogram {program_id}: {e}")
                pass
