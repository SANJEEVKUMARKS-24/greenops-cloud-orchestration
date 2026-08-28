from abc import ABC, abstractmethod


class Scheduler(ABC):

    @abstractmethod
    def decide(self, job, candidate_regions, current_time):
        pass