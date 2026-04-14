# Tenant Lifecycle Support

Updated: 2026-04-15

## States

Support should recognize these tenant lifecycle states:

- `TRIALING`
- `ACTIVE`
- `GRACE`
- `SUSPENDED`

## Support Expectations By State

### `TRIALING`

- onboarding should proceed normally
- recurring setup should be completed before expiry

### `ACTIVE`

- normal owner and branch runtime behavior should be available within plan limits

### `GRACE`

- billing recovery should be the main support action
- owners may still need access to recovery-related surfaces
- runtime may be bounded by the grace posture

### `SUSPENDED`

- normal owner/runtime access may be blocked
- support should focus on confirming the suspension reason and billing/provider recovery path

## Evidence To Collect

- tenant name
- current lifecycle state shown in the product
- recent billing/provider action taken by the customer
- screenshot of the blocked surface

## Support Actions

1. confirm the lifecycle state shown by the product
2. confirm whether the customer expects trial, active, grace, or suspended behavior
3. if provider/billing state is clearly inconsistent, escalate to the billing/provider owner
4. if the state is correct but the customer does not understand the consequence, explain the expected recovery path

## Escalate When

- a tenant is clearly in the wrong lifecycle state
- a successful recovery/payment is not reflected in product state
- runtime remains blocked after lifecycle recovery appears complete
