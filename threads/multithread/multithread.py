#!/usr/bin/env python3

import concurrent.futures
import threading

max_workers = 8
sema = threading.Semaphore(max_workers)
next_million = 0
next_million_lock = threading.Lock()
found = None


def find(millions: int) -> None:
  global found

  begin = millions * 1_000_000
  end = begin + 1_000_000
  print(f"{begin}-{end}: Finding...")

  if found is not None:
    print(f"{begin}-{end}: Found already")
    return None

  for i in range(begin, end):
    if i == 31_415_926:
      print(f"{begin}-{end}: Found {i}")
      found = True
      return

  print(f"{begin}-{end}: Not found")


def main():
  global next_million

  executor = concurrent.futures.ThreadPoolExecutor(max_workers)
  while found is None:
    sema.acquire()
    with next_million_lock:
      future = executor.submit(find, next_million)
      next_million += 1
    future.add_done_callback(lambda _: sema.release())
  executor.shutdown()

  if found is None:
    print("Not found")
    return

  print(f"Found: {found}")


if __name__ == "__main__":
  main()
