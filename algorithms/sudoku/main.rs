use std::{
  fmt,
  io::Read,
  ops::{Index, IndexMut},
};

#[derive(Clone)]
struct Sudoku {
  grid: [[u8; 9]; 9],
}

impl Sudoku {
  fn new() -> Self {
    Sudoku { grid: [[0; 9]; 9] }
  }

  fn is_valid(&self) -> bool {
    for i in 0..9 {
      let mut row_check = [false; 10];
      let mut col_check = [false; 10];
      let mut box_check = [false; 10];

      for j in 0..9 {
        let row_value = self[(i, j)] as usize;
        if row_value != 0 {
          if row_check[row_value] {
            return false;
          }
          row_check[row_value] = true;
        }

        let col_value = self[(j, i)] as usize;
        if col_value != 0 {
          if col_check[col_value] {
            return false;
          }
          col_check[col_value] = true;
        }

        let box_row = (i / 3) * 3 + j / 3;
        let box_col = (i % 3) * 3 + j % 3;
        let box_value = self.grid[box_row][box_col] as usize;
        if box_value != 0 {
          if box_check[box_value] {
            return false;
          }
          box_check[box_value] = true;
        }
      }
    }
    true
  }

  fn is_solved(&self) -> bool {
    for i in 0..9 {
      for j in 0..9 {
        if self[(i, j)] == 0 {
          return false;
        }
      }
    }
    true
  }

  fn solve(&self) -> Option<Self> {
    if self.is_solved() {
      return Some(self.clone());
    }
    if !self.is_valid() {
      return None;
    }
    let mut copy = self.clone();
    for i in 0..9 {
      for j in 0..9 {
        if copy[(i, j)] == 0 {
          for num in 1..=9 {
            copy[(i, j)] = num;
            if let Some(solution) = copy.solve() {
              return Some(solution);
            }
          }
          return None;
        }
      }
    }
    None
  }
}

impl Index<(usize, usize)> for Sudoku {
  type Output = u8;

  fn index(&self, index: (usize, usize)) -> &Self::Output {
    &self.grid[index.0][index.1]
  }
}

impl IndexMut<(usize, usize)> for Sudoku {
  fn index_mut(&mut self, index: (usize, usize)) -> &mut Self::Output {
    &mut self.grid[index.0][index.1]
  }
}

impl fmt::Display for Sudoku {
  fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
    write!(f, "+-------+-------+-------+\n")?;
    for i in 0..9 {
      write!(f, "| ")?;
      for j in 0..9 {
        let value = self[(i, j)];
        if value == 0 {
          write!(f, ".")?;
        } else {
          write!(f, "{}", value)?;
        }
        write!(f, " ")?;
        if (j + 1) % 3 == 0 && j < 8 {
          write!(f, "| ")?;
        }
      }
      write!(f, "|\n")?;
      if (i + 1) % 3 == 0 && i < 8 {
        write!(f, "+-------+-------+-------+\n")?;
      }
    }
    write!(f, "+-------+-------+-------+\n")?;
    Ok(())
  }
}

fn main() {
  let mut sudoku = Sudoku::new();
  for i in 0..9 {
    for j in 0..9 {
      let value = loop {
        let Some(Ok(byte)) = std::io::stdin().bytes().next() else {
          panic!("Failed to read input");
        };
        if byte.is_ascii_whitespace() {
          continue;
        }
        break if byte.is_ascii_digit() {
          byte - b'0'
        } else {
          0
        };
      };
      sudoku[(i, j)] = value;
    }
  }
  let sudoku = sudoku;

  println!("Original:");
  println!("{}", sudoku);
  if let Some(solution) = sudoku.solve() {
    println!("Solved:");
    println!("{}", solution);
  } else {
    println!("No solution found");
  }
}
