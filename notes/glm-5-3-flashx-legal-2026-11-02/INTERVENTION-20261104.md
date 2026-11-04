# Intervention, 4 Nov 2026 (Daniel approved in souls.house jbamre, eGxPNY)

Two freeflow samples, VARY_12 and LONG_22, ended finish_length at the declared
32,768-token ceiling on every attempt: the model spent the whole budget on hidden
reasoning (numbering the words of its own drafts) and returned no answer.
Daniel approved raising the ceiling for those two only. The freeflow token policy
in models/glm-5-3-flashx-legal-or-pin-zai.json went from [16000, 32768] to
[16000, 32768, 65536, 131072] (131,072 = the Z.AI endpoint's max completion), the
spec input hash was updated to match, and the two samples were given two extra
tries through recover_blocked.py (authorization daniel-jbamre-eGxPNY-20261104).
Originals: models/*.pre-repair-20261104.json, spec.pre-repair-20261104.json,
and the earlier attempts under the phase raw_attempts directory. The other 123
freeflow samples and all 120 values samples are untouched. Same precedent as the
Qwen3.8-27B LONG repair of 23 Sep 2026.

Run contract: state meta spec fingerprint moved 0da5188caab48e19d136ae64e17875aff5ca98b9da42bf3f62dbc8a10aac0a09 -> 163db19332691516cd560184bf7220c7bcd96535246e02e4ea6d6886a779bd2a (the only spec change is the input hash above; pre-repair state copy at state.pre-repair-20261104.sqlite).
