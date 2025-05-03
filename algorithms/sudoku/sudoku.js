class Sudoku {
  constructor() {
    this.board = Array(9).fill().map(() => Array(9).fill(0));
  }

  clone() {
    const copy = new Sudoku();
    for (let i = 0; i < 9; ++i) {
      for (let j = 0; j < 9; ++j) {
        copy.board[i][j] = this.board[i][j];
      }
    }
    return copy;
  }

  getValue(pos) {
    return this.board[pos[0]][pos[1]];
  }

  setValue(pos, value) {
    this.board[pos[0]][pos[1]] = value;
    return value;
  }

  isValid() {
    for (let i = 0; i < 9; ++i) {
      const rowCheck = Array(10).fill(false);
      const colCheck = Array(10).fill(false);
      const boxCheck = Array(10).fill(false);

      for (let j = 0; j < 9; ++j) {
        const rowValue = this.getValue([i, j]);
        if (rowValue !== 0) {
          if (rowCheck[rowValue]) {
            return false;
          }
          rowCheck[rowValue] = true;
        }

        const colValue = this.getValue([j, i]);
        if (colValue !== 0) {
          if (colCheck[colValue]) {
            return false;
          }
          colCheck[colValue] = true;
        }

        const boxRow = Math.floor(i / 3) * 3 + Math.floor(j / 3);
        const boxCol = (i % 3) * 3 + (j % 3);
        const boxValue = this.getValue([boxRow, boxCol]);
        if (boxValue !== 0) {
          if (boxCheck[boxValue]) {
            return false;
          }
          boxCheck[boxValue] = true;
        }
      }
    }
    return true;
  }

  isSolved() {
    for (let i = 0; i < 9; ++i) {
      for (let j = 0; j < 9; ++j) {
        if (this.getValue([i, j]) === 0) {
          return false;
        }
      }
    }
    return this.isValid();
  }

  solve() {
    if (this.isSolved()) {
      return this;
    }
    if (!this.isValid()) {
      return null;
    }

    const copy = this.clone();
    for (let i = 0; i < 9; ++i) {
      for (let j = 0; j < 9; ++j) {
        if (copy.getValue([i, j]) === 0) {
          for (let num = 1; num <= 9; ++num) {
            copy.setValue([i, j], num);
            const result = copy.solve();
            if (result !== null) {
              return result;
            }
            copy.setValue([i, j], 0);
          }
          return null;
        }
      }
    }
    return null;
  }

  toString() {
    let result = "+-------+-------+-------+\n";
    for (let i = 0; i < 9; ++i) {
      result += "| ";
      for (let j = 0; j < 9; ++j) {
        const value = this.getValue([i, j]);
        result += value === 0 ? "." : value;
        result += " ";
        if ((j + 1) % 3 === 0 && j < 8) {
          result += "| ";
        }
      }
      result += "|\n";
      if ((i + 1) % 3 === 0 && i < 8) {
        result += "+-------+-------+-------+\n";
      }
    }
    result += "+-------+-------+-------+\n";
    return result;
  }
}

function main() {
  const sudoku = new Sudoku();
  let inputBuffer = "";
  let rowIndex = 0;
  let colIndex = 0;

  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    inputBuffer += chunk;

    while (inputBuffer.length > 0 && rowIndex < 9) {
      const char = inputBuffer[0];
      inputBuffer = inputBuffer.slice(1);
      if (/\s/.test(char)) {
        continue;
      }
      if (/[1-9]/.test(char)) {
        const value = parseInt(char, 10);
        sudoku.setValue([rowIndex, colIndex], value);

        ++colIndex;
        if (colIndex === 9) {
          colIndex = 0;
          ++rowIndex;
        }
      }
    }

    if (rowIndex === 9) {
      process.stdin.pause();

      // Display and solve the puzzle
      console.log("Original:");
      console.log(sudoku.toString());

      const result = sudoku.solve();
      if (result === null) {
        console.log("No solution found.");
        process.exit(1);
      }

      console.log("Solved:");
      console.log(result.toString());
      process.exit(0);
    }
  });

  process.stdin.on("end", () => {
    if (rowIndex < 9) {
      console.error("Unexpected EOF");
      process.exit(1);
    }
  });
}

main();
