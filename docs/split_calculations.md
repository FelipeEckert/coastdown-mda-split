# Split Calculation Sign Convention

## Delta V Storage

The application stores and displays `Delta V` as a positive interval amplitude:

```text
Delta V = abs(V_initial - V_final)
```

This convention is used in parser traceability, UI tables, validation messages,
and exported reports. It avoids exposing negative interval widths to the user.

## Normative Deceleration Convention

The Split equations describe a deceleration event. In the normative derivation,
the velocity variation over time is signed:

```text
dv/dt = -Delta V / Delta t
```

If the software stores `Delta V` as a positive amplitude, using the textual
equation directly would produce the opposite sign for the road-load
coefficients. The implementation therefore uses the equivalent road-load-positive
form:

```text
a1 = Delta V1 / Delta t1
a2 = Delta V2 / Delta t2

f'0 = Me / (V2^2 - V1^2) * (a1 * V2^2 - a2 * V1^2)
f'2 = Me / (V2^2 - V1^2) * (a2 - a1)
```

This is equivalent to substituting `dvdt1 = -Delta V1 / Delta t1` and
`dvdt2 = -Delta V2 / Delta t2` into the signed deceleration equation, then
returning positive road-load coefficients. The code must not use an unexplained
final sign flip such as `return -f0_raw, -f2_raw`.

## Reference Case

For:

```text
Me = 1545 kg
Delta t1 = 19.58 s
Delta t2 = 18.72 s
V1 = 40 km/h
V2 = 80 km/h
Delta V1 = 10 km/h
Delta V2 = 20 km/h
```

Expected:

```text
f'0 = 139.41119395239252 N
f'2 = 0.6461779091694823 N/(m/s)^2
```
