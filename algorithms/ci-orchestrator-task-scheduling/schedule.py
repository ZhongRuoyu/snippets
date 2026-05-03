#!/usr/bin/env python3

import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from random import random
from threading import Condition, Lock, Thread
from time import sleep


class QueueType(Enum):
  MacOS_Arm64 = auto()
  MacOS_x86_64 = auto()

  def slots(self) -> int:
    if self in (QueueType.MacOS_Arm64, QueueType.MacOS_x86_64):
      return 12
    return 0

  @staticmethod
  def from_str(s: str) -> "QueueType":
    if s == "macos-arm64":
      return QueueType.MacOS_Arm64
    if s == "macos-x86_64":
      return QueueType.MacOS_x86_64
    raise ValueError

  def __str__(self) -> str:
    if self == QueueType.MacOS_Arm64:
      return "macos-arm64"
    if self == QueueType.MacOS_x86_64:
      return "macos-x86_64"
    raise ValueError


class PriorityType(Enum):
  Long = auto()
  Dispatch = auto()
  Default = auto()

  @staticmethod
  def from_str(s: str) -> "PriorityType":
    if s == "long":
      return PriorityType.Long
    if s == "dispatch":
      return PriorityType.Dispatch
    if s == "default":
      return PriorityType.Default
    raise ValueError

  def __str__(self) -> str:
    if self == PriorityType.Long:
      return "long"
    if self == PriorityType.Dispatch:
      return "dispatch"
    if self == PriorityType.Default:
      return "default"
    raise ValueError


@dataclass
class Job:
  id: int
  priority: PriorityType
  duration: float
  data: str

  def run(self, callback: Callable[["Job"], None]) -> None:
    sleep((self.duration + random()) / 10)  # noqa: S311
    callback(self)

  def __repr__(self) -> str:
    return f"Job({self.priority}, {self.data})"


@dataclass
class SharedState:
  running_jobs: dict[QueueType, list[Job]]
  running_jobs_mutex: Lock
  threads: list[Thread]
  threads_mutex: Lock
  should_join: bool
  should_join_mutex: Lock

  def __init__(self) -> None:
    self.running_jobs = {queue_type: [] for queue_type in QueueType}
    self.running_jobs_mutex = Lock()
    self.threads = []
    self.threads_mutex = Lock()
    self.should_join = False
    self.should_join_mutex = Lock()

  def join(self) -> None:
    with self.should_join_mutex:
      self.should_join = True
    with self.threads_mutex:
      for t in self.threads:
        t.join()

  def __repr__(self) -> str:
    jobs_by_queue = {
      str(queue_type): {
        str(priority): sum(1 for job in jobs if job.priority == priority)
        for priority in PriorityType
      }
      for queue_type, jobs in self.running_jobs.items()
    }
    return str(jobs_by_queue)


class JobQueue:
  mutex: Lock
  queue: dict[PriorityType, list[Job]]
  queue_type: QueueType
  condvar: Condition
  shared_state: SharedState

  QUARTER_SLOTS: int
  HALF_SLOTS: int

  def __init__(self, shared_state: SharedState, queue_type: QueueType) -> None:
    self.mutex = Lock()
    self.queue = {priority_type: [] for priority_type in PriorityType}
    self.queue_type = queue_type
    self.condvar = Condition(self.mutex)
    self.shared_state = shared_state

    self.HALF_SLOTS = queue_type.slots() // 2
    self.QUARTER_SLOTS = queue_type.slots() // 4

  def push(self, job: Job) -> None:
    with self.mutex:
      self.queue[job.priority].append(job)
      print(f"{job} queued")
      print(f"Queue: {self}")
      print()
      self.condvar.notify_all()

  def pop(self) -> Job | None:
    with self.mutex:
      while True:
        with self.shared_state.should_join_mutex:
          if self.shared_state.should_join:
            return None

        with self.shared_state.running_jobs_mutex:
          running_jobs = self.shared_state.running_jobs[self.queue_type]
          running_long_build_count = sum(
            1 for job in running_jobs if job.priority == PriorityType.Long
          )
          running_dispatch_build_count = sum(
            1 for job in running_jobs if job.priority == PriorityType.Dispatch
          )

        has_long_jobs = len(self.queue[PriorityType.Long]) > 0
        has_dispatch_jobs = len(self.queue[PriorityType.Dispatch]) > 0

        if has_long_jobs and has_dispatch_jobs:
          # Both have jobs: each gets 25%
          long_slot_limit = dispatch_slot_limit = self.QUARTER_SLOTS
        elif has_long_jobs:
          # Dispatch empty: long gets 50%
          long_slot_limit = self.HALF_SLOTS
          dispatch_slot_limit = 0
        elif has_dispatch_jobs:
          # Long empty: dispatch gets 50%
          dispatch_slot_limit = self.HALF_SLOTS
          long_slot_limit = 0
        else:
          # Both empty: only schedule default jobs
          long_slot_limit = dispatch_slot_limit = 0

        if (
          running_long_build_count + running_dispatch_build_count
          < self.HALF_SLOTS
        ):
          should_schedule_long = (
            has_long_jobs and running_long_build_count < long_slot_limit
          )
          if should_schedule_long:
            return self.run(self.queue[PriorityType.Long].pop(0))

          should_schedule_dispatch = (
            has_dispatch_jobs
            and running_dispatch_build_count < dispatch_slot_limit
          )
          if should_schedule_dispatch:
            return self.run(self.queue[PriorityType.Dispatch].pop(0))

        # Fill remaining slots with default jobs
        if len(self.queue[PriorityType.Default]) > 0:
          return self.run(self.queue[PriorityType.Default].pop(0))

        self.condvar.wait()

  def run(self, job: Job) -> Job:
    with self.shared_state.running_jobs_mutex:
      self.shared_state.running_jobs[self.queue_type].append(job)
      print(f"{job} started")
      print(f"State: {self.shared_state}")
      print(f"Queue: {self}")
      print()
    return job

  def join(self) -> None:
    while len(self) > 0:
      with self.mutex:
        self.condvar.wait()
    with self.mutex:
      self.condvar.notify_all()

  def __len__(self) -> int:
    with self.mutex:
      return sum(len(jobs) for jobs in self.queue.values())

  def __repr__(self) -> str:
    summary = str(
      {
        priority_type.name: len(jobs)
        for priority_type, jobs in self.queue.items()
      },
    )
    return f"JobQueue({self.queue_type}, {summary})"


def to_job(line: str) -> tuple[QueueType, Job] | None:
  parts = line.split()
  if len(parts) != 4:  # noqa: PLR2004
    return None

  try:
    queue_type = QueueType.from_str(parts[0].strip())
    priority = PriorityType.from_str(parts[1].strip())
    duration = float(parts[2].strip())
    data = parts[3].strip()
  except ValueError:
    return None

  job_id = getattr(to_job, "next_id", 1)
  setattr(to_job, "next_id", job_id + 1)  # noqa: B010
  return queue_type, Job(
    id=job_id,
    priority=priority,
    duration=duration,
    data=data,
  )


def to_sleep(line: str) -> float | None:
  parts = line.split()
  if len(parts) != 2:  # noqa: PLR2004
    return None
  return float(parts[1].strip())


def scheduler(shared_state: SharedState, queue: JobQueue) -> None:
  def callback(current_job: Job) -> None:
    with shared_state.running_jobs_mutex:
      shared_state.running_jobs[queue.queue_type].remove(current_job)
      print(f"{current_job} finished")
      print(f"State: {shared_state}")
      print()
    with queue.mutex:
      queue.condvar.notify_all()

  while True:
    while True:
      with shared_state.running_jobs_mutex:
        running_jobs_count = len(shared_state.running_jobs[queue.queue_type])
      if running_jobs_count < queue.queue_type.slots():
        break
      with queue.mutex:
        queue.condvar.wait()

    job = queue.pop()
    if job is None:
      return

    with shared_state.threads_mutex:
      job_thread = Thread(target=lambda job: job.run(callback), args=(job,))
      shared_state.threads.append(job_thread)
      job_thread.start()


def main() -> None:
  shared_state = SharedState()
  queues = {
    QueueType.MacOS_Arm64: JobQueue(shared_state, QueueType.MacOS_Arm64),
    QueueType.MacOS_x86_64: JobQueue(shared_state, QueueType.MacOS_x86_64),
  }
  scheduler_threads = {
    queue_type: Thread(target=scheduler, args=(shared_state, queue))
    for queue_type, queue in queues.items()
  }
  for scheduler_thread in scheduler_threads.values():
    scheduler_thread.start()

  if sys.stdin.isatty():
    print("To add a job, enter: <queue-type> <priority> <duration> <data>")
    print('For example: "macos-arm64 long 10 long-job-1"')
  try:
    while True:
      if sys.stdin.isatty():
        print("> ", end="", flush=True)
      line = input().strip()
      if line.startswith("#") or line == "":
        continue

      sleep_duration = to_sleep(line)
      if sleep_duration is not None:
        sleep((sleep_duration + random()) / 10)  # noqa: S311
        continue

      job_result = to_job(line)
      if job_result is not None:
        queue_type, job = job_result
        queues[queue_type].push(job)
        continue

      print(f"Invalid job: {line}")
  except (EOFError, KeyboardInterrupt):
    if sys.stdin.isatty():
      print()
    for queue in queues.values():
      queue.join()
    shared_state.join()
    for scheduler_thread in scheduler_threads.values():
      scheduler_thread.join()


if __name__ == "__main__":
  main()
