#pragma once

#include <optional>
#include <string>
#include <vector>

struct Setting {
    std::string setup_question;
    std::string help_string;
    std::string token;
    std::string offset;
    std::string width;

    std::optional<std::string> bios_default;
    std::vector<std::string> options;
    std::optional<std::size_t> active_option;
    std::optional<std::string> value;
    std::vector<std::string> content;

    std::string unique_id() {
      return setup_question + "||" + token + "||" + offset;
    }
};
