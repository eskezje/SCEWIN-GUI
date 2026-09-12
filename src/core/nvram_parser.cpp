#include "nvram_parser.hpp"
#include "core/setting.hpp"

#include <cstddef>
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

std::string trim(const std::string &str) {
  const auto first = str.find_first_not_of(" \t\r\n");
  if (first == std::string::npos) {
    return "";
  }
  const auto last = str.find_last_not_of(" \t\r\n");
  return str.substr(first, last - first + 1);
}

void finalize_setting(std::optional<Setting> &current_setting,
                      std::vector<Setting> &settings) {
  if (!current_setting) {
    return;
  }
  if (current_setting->options.size() == 1 && !current_setting->active_option) {
    // i dont remember why i did this in my python version
    // checking if there is only 1 option, and then if there is no option chosen
    current_setting->value = current_setting->options[0];
    current_setting->options.clear();
  }
  // copy the completed setting to the vector of settings
  settings.push_back(*current_setting);
  // clear our current setting to be optional such as None
  current_setting.reset();
}

void parse_options_line(const std::string &line, Setting &setting) {
  std::smatch match;

  if (std::regex_match(line, match, patterns.option)) {
    std::string star = match[1].str();
    std::string bracket_num = match[2].str();
    std::string remainder = match[3].str();

    std::string option = "[" + bracket_num + "]" + remainder;
    option = trim(option);

    std::size_t index = setting.options.size();
    setting.options.push_back(option);

    if (star == "*") {
      setting.active_option = index;
    }

    return;
  }

  // fallback
  std::string cleaned = trim(line);

  if (cleaned.empty()) {
    return;
  }

  bool active = cleaned.front() == '*';
  std::string option = cleaned;

  if (active) {
    option.erase(0, 1);
    option = trim(option);
  }

  if (option.empty()) {
    return;
  }

  std::size_t index = setting.options.size();
  setting.options.push_back(option);

  if (active) {
    setting.active_option = index;
  }
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

  while (std::getline(file, line)) {
    // removing comment
    line = std::regex_replace(line, patterns.comment, "");
    // remove whitespace at front and at end
    line = trim(line);
    // check if there is anything
    if (line.empty()) {
      continue;
    }

    // setup question
    if (std::regex_match(line, match, patterns.setup_question)) {
      // handle the setting
      finalize_setting(current_setting, settings);

      current_setting = Setting{};
      current_setting->setup_question = trim(match[1].str());
      continue;
    }

    if (!current_setting) {
      continue;
    }

    // help string
    if (std::regex_match(line, match, patterns.help_string)) {
      current_setting->help_string = trim(match[1].str());
      continue;
    }

    // token
    if (std::regex_match(line, match, patterns.token)) {
      current_setting->token = trim(match[1].str());
      continue;
    }

    // offset
    if (std::regex_match(line, match, patterns.offset)) {
      current_setting->offset = trim(match[1].str());
      continue;
    }

    // width
    if (std::regex_match(line, match, patterns.width)) {
      current_setting->width = trim(match[1].str());
      continue;
    }

    // bios default
    if (std::regex_match(line, match, patterns.bios_default)) {
      current_setting->bios_default = trim(match[1].str());
      continue;
    }

    // first options line
    if (std::regex_match(line, match, patterns.options)) {
      std::string remainder = trim(match[1].str());
      parse_options_line(remainder, *current_setting);
      continue;
    }

    // value
    if (std::regex_match(line, match, patterns.value)) {
      current_setting->value = trim(match[1].str());
      continue;
    }

    // other options
    if (std::regex_match(line, match, patterns.bracket_option)) {
      parse_options_line(line, *current_setting);
      continue;
    }

    // anything else we will add to content
    current_setting->content.push_back(line);
  }

  finalize_setting(current_setting, settings);

  return settings;
}
