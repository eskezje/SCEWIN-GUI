#include "nvram_parser.hpp"

#include <fstream>
#include <stdexcept>

std::vector<Setting> parse_nvram(const std::string &path)
{
    // open file from path
    std::ifstream file(path);
    // check if file could open
    if (!file.is_open())
    {
        throw std::runtime_error("could not open file");
    }
    std::vector<Setting> settings;
    // parsing here

    
    return settings;
}