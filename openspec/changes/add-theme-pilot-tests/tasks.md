# Tasks: Add Theme Modal Pilot Tests

## 1. Core Theme Modal Tests

- [x] 1.1 Test opening theme modal and verifying OptionList is focused
- [x] 1.2 Test scrolling down through theme list (j or down arrow)
- [x] 1.3 Test scrolling up through theme list (k or up arrow)
- [x] 1.4 Test that current theme is highlighted with marker on open
- [x] 1.5 Test selecting current theme (no change expected)
- [x] 1.6 Test selecting different theme (theme property changes)
- [x] 1.7 Test escape cancels without changing theme

## 2. Search Bar State Preservation

- [x] 2.1 Test empty search bar preserved after theme open/close (escape)
- [x] 2.2 Test text in search bar preserved after theme open/close (escape)
- [x] 2.3 Test text in search bar preserved after selecting same theme
- [x] 2.4 Test text in search bar preserved after selecting different theme
- [x] 2.5 Test no garbage/wacky characters appear in search bar after theme selection (bug verification)

## 3. Edge Cases and Variations

- [x] 3.1 Test rapid theme modal open/close cycles
- [x] 3.2 Test scroll to top of list, try scrolling up further
- [x] 3.3 Test scroll to bottom of list, try scrolling down further
- [x] 3.4 Test selecting theme while search results are displayed
- [x] 3.5 Test theme persistence via settings (verify save_settings called)
