"""
GameClock class for the NFL Football Simulation
"""


class GameClock:
    """Manages game time and quarters"""

    def __init__(self):
        self.quarter = 1
        self.time_remaining = 15 * 60  # 15 minutes in seconds
        self.two_min_warning_shown = [False, False, False, False]

    def format_time(self):
        """Format time as Q# - MM:SS"""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return f"Q{self.quarter} - {minutes}:{seconds:02d}"

    def run_time(self, seconds):
        """Run time off the clock, returns True if clock stops"""
        self.time_remaining -= seconds

        # Check for 2-minute warning
        if self.time_remaining <= 120 and not self.two_min_warning_shown[self.quarter - 1]:
            self.two_min_warning_shown[self.quarter - 1] = True
            return True  # Clock stops

        if self.time_remaining <= 0:
            if self.quarter < 4:
                self.quarter += 1
                self.time_remaining = 15 * 60
            else:
                return False  # Game over
        return False

    def is_game_over(self):
        """Check if game is over"""
        return self.quarter > 4 or (self.quarter == 4 and self.time_remaining <= 0)

    def is_half_over(self):
        """Check if half just ended"""
        return self.quarter == 3 and self.time_remaining == 15 * 60
