# Home Linux deployment design

Status: proposed, awaiting review and verification. The owner intends to use a Linux system; the distribution and target machine have not yet been selected. The current live implementation and evidence target Ubuntu with `journalctl -u ssh` and systemd. Other distributions may use a different SSH unit, journal, service manager or log format and require explicit compatibility work and tests.

## Proposed private access

Keep the dashboard bound to loopback on the Linux system. Tailscale Serve can provide HTTPS to authorized devices on the owner's tailnet and proxy to the local dashboard. The existing Heimdall owner login remains required. Tailnet access policy must be reviewed for the intended devices. Tailscale documents the proxy and access controls in its [Serve examples](https://tailscale.com/docs/reference/examples/serve) and [access control guide](https://tailscale.com/docs/features/access-control).

The dashboard currently accepts only its configured local HTTP Host and Origin. A Tailscale HTTPS hostname will fail those checks. A reviewed implementation must explicitly configure the permitted external HTTPS origin, validate the Host and Origin against it, secure the session cookie for HTTPS, and avoid trusting arbitrary forwarded headers. Retain the current local mode and its checks. Test login, protected actions, rejection of other hosts and origins, and session behavior through the proxy before deployment.

Tailscale documents background Serve configuration as resuming after a reboot in its [CLI reference](https://tailscale.com/docs/reference/tailscale-cli/serve). The dashboard itself also needs an independently reviewed startup mechanism for the selected system. Monitoring and terminal access must remain usable without Tailscale. No configuration has been applied.

## Verification before completion

- Identify the Linux distribution, SSH log source and service manager. Verify prerequisites and permissions without assuming all Linux systems behave like Ubuntu.
- Review dashboard startup and the private access configuration with the owner before changing device or network settings.
- Verify remote HTTPS login and dashboard operations, rejection from outside the authorized tailnet, and startup after a restart.
- Disconnect Tailscale and verify local monitoring and terminal access. Record results and limitations in issue #16.
