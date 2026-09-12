#pragma once

#include "setting.hpp"

#include <string>
#include <vector>

std::vector<Setting> parse_nvram(const std::string& path);
