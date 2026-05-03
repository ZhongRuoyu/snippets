import std;

int main() {
  std::vector<int> v{1, 2, 3};
  for (const auto &e : v) {
    std::cout << e << " ";
  }
  std::cout << "\n";
}
