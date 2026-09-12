#include "nvram_parser.hpp"

#include <fstream>
#include <optional>
#include <regex>
#include <stdexcept>
#include <string>

namespace {

struct ParserRegex {
  std::regex comment;
  std::regex setup_question;
  std::regex help_string;
  std::regex token;
  std::regex offset;
  std::regex width;
  std::regex bios_default;
  std::regex options;
  std::regex value;
  std::regex bracket_option;
  std::regex option;
};

const ParserRegex patterns{
    .comment = std::regex(R"((\s*)(//.*)?$)"),
    .setup_question =
        std::regex(R"(^Setup\s+Question\s*=\s*(.*))", std::regex::icase),
    .help_string =
        std::regex(R"(^Help\s+String\s*=\s*(.*))", std::regex::icase),
    .token = std::regex(R"(^Token\s*=\s*(.*))", std::regex::icase),
    .offset = std::regex(R"(^Offset\s*=\s*(.*))", std::regex::icase),
    .width = std::regex(R"(^Width\s*=\s*(.*))", std::regex::icase),
    .bios_default =
        std::regex(R"(^BIOS\s+Default\s*=\s*(.*))", std::regex::icase),
    .options = std::regex(R"(^Options\s*=\s*(.*))", std::regex::icase),
    .value = std::regex(R"(^Value\s*=\s*(.*))", std::regex::icase),
    .bracket_option = std::regex(R"(^\**\[(.*?)\](.*))"),
    .option = std::regex(R"((\*?)\[([^\]]+)\](\S.*?|)$)")};

std::string trim(const std::string& str)
{
    const auto first = str.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return "";
    }
    const auto last = str.find_last_not_of(" \t\r\n");
    return str.substr(first, last - first + 1);
}

} // namespace

std::vector<Setting> parse_nvram(const std::string &path) {
  // open file from path
  std::ifstream file(path);
  // check if file could open
  if (!file.is_open()) {
    throw std::runtime_error("could not open file" + path);
  }
  std::vector<Setting> settings;
  std::optional<Setting> current_setting;
  // parsing here
  std::string line;
  std::smatch match;

  while (std::getline(file,line)) {
    // removing comment
    line = std::regex_replace(line, patterns.comment, "");
    // remove whitespace at front and at end
    line = trim(line);
    // setup question 
    if (std::regex_match(line, match, patterns.setup_question)) {
      // handle the setting 
    }
  }

  return settings;
}
