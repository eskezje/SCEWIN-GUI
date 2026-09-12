#include "core/nvram_parser.hpp"

#include <exception>
#include <iostream>

int main()
{
    try {
        auto settings = parse_nvram("test_files/nvram_test.txt");
        std::cout << "parsed " << settings.size() << " settings\n";
    }
    catch (std::exception& except) {
        std::cerr << "error: " << except.what() << '\n';
        return 1;
    }

    return 0;
}