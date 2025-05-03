#include <array>
#include <bitset>
#include <cctype>
#include <iostream>
#include <optional>
#include <ostream>
#include <utility>

class Sudoku {
 public:
  int &operator[](std::pair<int, int> pos) {
    return this->board_[pos.first][pos.second];
  }

  [[nodiscard]] int operator[](std::pair<int, int> pos) const {
    return this->board_[pos.first][pos.second];
  }

  [[nodiscard]] bool IsValid() const {
    for (int i = 0; i < 9; ++i) {
      std::bitset<10> row_check = {};
      std::bitset<10> col_check = {};
      std::bitset<10> box_check = {};

      for (int j = 0; j < 9; ++j) {
        int row_value = (*this)[{i, j}];
        if (row_value != 0) {
          if (row_check[row_value]) {
            return false;
          }
          row_check[row_value] = true;
        }

        int col_value = (*this)[{j, i}];
        if (col_value != 0) {
          if (col_check[col_value]) {
            return false;
          }
          col_check[col_value] = true;
        }

        int box_row = ((i / 3) * 3) + (j / 3);
        int box_col = ((i % 3) * 3) + (j % 3);
        int box_value = (*this)[{box_row, box_col}];
        if (box_value != 0) {
          if (box_check[box_value]) {
            return false;
          }
          box_check[box_value] = true;
        }
      }
    }

    return true;
  }

  [[nodiscard]] bool IsSolved() const {
    for (int i = 0; i < 9; ++i) {
      for (int j = 0; j < 9; ++j) {
        if ((*this)[{i, j}] == 0) {
          return false;
        }
      }
    }
    return this->IsValid();
  }

  [[nodiscard]] std::optional<Sudoku> Solve() const {
    if (this->IsSolved()) {
      return *this;
    }
    if (!this->IsValid()) {
      return {};
    }
    Sudoku copy = *this;
    for (int i = 0; i < 9; ++i) {
      for (int j = 0; j < 9; ++j) {
        if (copy[{i, j}] == 0) {
          for (int num = 1; num <= 9; ++num) {
            copy[{i, j}] = num;
            std::optional<Sudoku> result = copy.Solve();
            if (result.has_value()) {
              return result;
            }
            copy[{i, j}] = 0;
          }
          return {};
        }
      }
    }
    return {};
  }

 private:
  std::array<std::array<int, 9>, 9> board_ = {};
};

std::ostream &operator<<(std::ostream &os, const Sudoku &sudoku) {
  os << "+-------+-------+-------+\n";
  for (int i = 0; i < 9; ++i) {
    os << "| ";
    for (int j = 0; j < 9; ++j) {
      int value = sudoku[{i, j}];
      if (value == 0) {
        os << ".";
      } else {
        os << value;
      }
      os << " ";
      if ((j + 1) % 3 == 0 && j < 8) {
        os << "| ";
      }
    }
    os << "|\n";
    if ((i + 1) % 3 == 0 && i < 8) {
      os << "+-------+-------+-------+\n";
    }
  }
  os << "+-------+-------+-------+\n";
  return os;
}

int main() {
  Sudoku sudoku;

  for (int i = 0; i < 9; ++i) {
    for (int j = 0; j < 9; ++j) {
      int value;
      for (;;) {
        value = std::cin.get();
        if (value == std::char_traits<char>::eof()) {
          std::cerr << "Unexpected EOF\n";
          return 1;
        }
        // NOLINTNEXTLINE(readability-implicit-bool-conversion)
        if (std::isspace(value)) {
          continue;
        }
        break;
      }
      // NOLINTNEXTLINE(readability-implicit-bool-conversion)
      if (std::isdigit(value)) {
        sudoku[{i, j}] = value - '0';
      }
    }
  }

  std::cout << "Original:\n" << sudoku << "\n";
  std::optional<Sudoku> result = sudoku.Solve();
  if (!result.has_value()) {
    std::cout << "No solution found\n";
    return 1;
  }
  std::cout << "Solved:\n" << *result << "\n";
}
