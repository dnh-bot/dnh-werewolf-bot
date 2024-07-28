---
name: New character
about: New character specs
title: 'New character - name_en (name_vi)'
labels: enhancement
assignees: ''

---

## Specs

`<spec here>`

## Checklist for new role

### Help text

- [ ] Update `json/role_info.json`
- [ ] Update `json/command_info.json`
- [ ] Update `STORY_VN.md`

### Code

- [ ] Create the new role class inside `game/roles/<rolename>.py` file
- [ ] Add new role class to `get_all_roles()` return result (inside `game/roles/__init__.py` file)
- [ ] Add new `<rolename>_do_(new|end)_(day|night)time_phase` function in `game/__init__.py` (if needed)
- If the new role has its command(s):
    - [ ] Add new command(s) in `commands/command.py`
    - [ ] Add new command action function(s) in `game/__init__.py`
- [ ] Update `json/text_template.json`

### Role generator

- [ ] Add new role point into `json/role_generator_info.json`
- [ ] Update `game/generate_roles.py` (if needed)
- [ ] Update `json/role_config.json` with the new role
- [ ] Run `evaluate_system()` inside `game/calc_points.py` and make sure the new role has been generated.

### Test cases

- [ ] simple test (follow specs)
- special cases (listed below)
    - [ ] the new role in a couple
    - [ ] the new role has a relation with other roles
