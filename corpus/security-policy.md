# Information Security Policy — Meridian Software Inc.

## Purpose

Meridian Software Inc. maintains this Information Security Policy to protect the confidentiality, integrity, and availability of company systems, customer data, source code, and internal business information. Security is a shared responsibility. Every employee, contractor with system access, and contingent worker who uses Meridian Software Inc. accounts or devices must follow the controls in this policy.

This document sets mandatory baseline requirements for authentication, device protection, incident reporting, data handling on removable media, and security awareness. It is written to be testable: managers, Internal Audit, and the Security Team can verify compliance against the specific timelines, lengths, and named controls below. The policy is administered with Pacific Time as the company’s headquarters timezone for interpreting “within 24 hours,” training due dates, and similar deadlines unless a control expressly uses business days.

Questions and exception requests should be directed to the Security Team. Lost or stolen devices and security incidents have dedicated reporting paths described later in this policy, including security@meridian-software.example.

## Scope

This policy applies to all workforce members who access Meridian Software Inc. email, VPN, source control, cloud environments, corporate endpoints, or nonpublic data. It applies whether work is performed in an office, at home, or while traveling. Third parties with access to company systems must meet equivalent controls under contract and technical onboarding requirements.

Systems in scope include, without limitation, corporate laptops and desktops, mobile devices used for company email or MFA, cloud admin consoles, code repositories, production and non-production environments that contain company or customer data, and collaboration tools tied to @meridian-software.example identities.

## Roles and Responsibilities

The Chief Information Security Officer (CISO) owns this policy and is accountable for its maintenance, exception governance, and alignment with Meridian Software Inc.’s risk posture. The Security Team implements monitoring, responds to incidents, runs phishing simulations, and evaluates exception requests. IT Service Desk provisions accounts, assists with encryption and MFA enrollment, and partners on device loss workflows. Managers ensure their teams complete training on time and escalate noncompliance. Individual users must protect credentials, report incidents on time, and never circumvent controls for convenience.

## Password Requirements

All Meridian Software Inc. passwords for company accounts must be at least 14 characters in length and must include at least one uppercase letter, one lowercase letter, one number, and one symbol. Passwords must not be based solely on dictionary words, sequential patterns, or easily discoverable personal data such as names or birthdays.

Password rotation is required every 90 days. Users must not reuse any of their last 12 passwords when setting a new password. Where a system cannot enforce the last-12 reuse prohibition technically, users are still prohibited from reuse and may be subject to corrective action if reuse is discovered during an investigation or audit.

Users must not share passwords or MFA codes with anyone, including managers, IT staff, or coworkers. IT and Security will never ask for a password in email or chat. Password managers approved by the Security Team are encouraged for generating and storing unique credentials. Writing passwords on sticky notes, storing them in unprotected personal notes, or placing them in shared documents is prohibited.

Service accounts and shared functional accounts, where unavoidable, must be inventoried by IT, owned by a named team, rotated on the same 90-day cadence unless a documented Security Team exception applies, and restricted to least privilege. Interactive daily work should be performed with individual named accounts, not shared passwords.

## Multi-Factor Authentication (MFA)

MFA is mandatory for email, VPN, source control, and cloud admin consoles. New accounts that grant access to any of these services must have MFA enabled within 24 hours of account creation. Access may be suspended if MFA is not completed within that window.

Users must enroll using Security-approved MFA methods. MFA devices and backup codes must be protected with the same care as passwords. If an MFA device is lost, the user must report the loss immediately through the incident and device-loss processes in this policy so that IT can revoke and re-enroll MFA.

MFA fatigue attacks and unsolicited MFA prompts must be treated as suspicious. Users who receive unexpected MFA push notifications must deny the request and report a suspected security incident within the required timeline.

## Device and Endpoint Protection

Company-issued computers must use full-disk encryption: BitLocker on Windows systems and FileVault on macOS systems. Encryption must remain enabled for the life of the device. Users must not disable encryption, decrypt drives for convenience, or postpone encryption setup after receiving a device. IT Service Desk will assist with recovery keys, which must be escrowed according to IT standards and must not be stored in unencrypted personal locations.

Screens must lock after 5 minutes of inactivity. Users must not extend the idle timeout beyond 5 minutes, and must lock the screen when leaving a device unattended even for brief periods. Clear desks and clear screens are expected in open offices and coworking spaces.

Users must keep operating systems and security agents up to date, install required patches within timelines communicated by IT, and must not disable endpoint detection, disk encryption, or portal management agents. Personal devices used for company email or other approved work must meet mobile security requirements published by IT, including device passcodes and remote-wipe capability where applicable.

## Removable Media and USB Storage

USB storage of Confidential or Restricted data is prohibited without a written exception from the Security Team. This prohibition includes thumb drives, external hard drives, and similar removable media, whether company-owned or personal. Users who believe a legitimate business need exists must request an exception before copying data, document the business justification, and follow any compensating controls the Security Team requires, such as encrypted media, inventory tracking, and time-limited approval.

Email, approved cloud collaboration platforms, and secure file transfer methods should be used instead of USB media whenever possible. Finding Confidential or Restricted data on unauthorized USB media is a security incident and must be reported under the incident timelines in this policy.

## Lost or Stolen Devices

If a laptop, phone, tablet, hardware token, or other device used for Meridian Software Inc. work is lost or stolen, the workforce member must report the loss within 1 hour to security@meridian-software.example and to the IT Service Desk. The report must include the approximate time and location of the loss, the device type, whether the device was likely unlocked, and whether Confidential or Restricted data may have been accessible.

Prompt reporting allows IT and Security to revoke sessions, rotate credentials, trigger remote wipe where available, and assess breach risk. Delayed reporting undermines containment and may result in corrective action, especially when delay is intentional or reckless.

Users traveling should maintain physical control of devices, use hotel safes when appropriate for storage of powered-off devices, and avoid leaving laptops unattended in vehicles. A device left behind in a rideshare or conference hall is treated as lost and must be reported within the 1-hour requirement once the loss is discovered.

## Suspected Security Incidents

A security incident includes, but is not limited to, malware infection, unauthorized access to accounts or systems, phishing that resulted in credential entry, ransomware indicators, accidental exposure of Confidential or Restricted data, MFA anomalies, and physical intrusion into areas containing sensitive systems.

Suspected security incidents must be reported within 4 hours of discovery to security@meridian-software.example, and users should also notify IT Service Desk when account or device action is needed. Employees must not attempt to “test” or “fix” a suspected compromise on their own in ways that destroy evidence, and must not pay ransom demands or communicate with attackers without explicit Security Team direction.

When reporting, provide known facts: what was observed, when it occurred, which systems and data may be involved, and any actions already taken. Preserve relevant emails and screenshots. Do not delete logs or reimage a machine before Security guidance unless necessary to stop active, severe harm, in which case the justification must be documented.

Managers who learn of a suspected incident from a team member must confirm that Security has been notified within the 4-hour window and must not suppress reporting to avoid embarrassment or customer communication concerns. External customer notifications, if required, are coordinated by the CISO and designated company leaders, not by individual contributors acting alone.

## Security Awareness Training

Annual security awareness training is mandatory. New hires must complete security awareness training within 30 days of hire. Thereafter, workforce members must complete training every 12 months. Managers are responsible for tracking completion in their teams and for escalating overdue training to People Operations and the Security Team.

Failure to complete training within required deadlines may result in progressive restrictions, including reduced system access, and may be reflected in performance management. Completing training is not optional even for senior leaders or technical experts; the baseline applies to all in-scope roles.

## Phishing Simulations

Meridian Software Inc. conducts phishing simulations to measure awareness and improve readiness. A workforce member who fails a phishing simulation must complete mandatory remediating training within 5 business days of notification. Repeated failures may trigger additional coaching, closer monitoring, or corrective action, depending on severity and pattern.

Users who realize they interacted with a real or simulated phishing message in a risky way should still report it promptly. Reporting real phishing is encouraged and will not be punished when done in good faith. Simulation failure remediation focuses on education; concealment of a real incident is treated far more seriously.

## Data Classification and Handling

Meridian Software Inc. classifies data to guide handling. While detailed classification standards may be published separately, this policy requires that Confidential and Restricted data receive heightened protection. Restricted data includes secrets such as production credentials, private keys, and sensitive personal data designated as Restricted by the company. Confidential data includes nonpublic business information that could harm the company or customers if disclosed.

Confidential and Restricted data must not be stored on personal cloud accounts, personal email, or unapproved messaging apps. Source code and customer data must remain within approved repositories and environments. Downloads to local disk must be minimized, protected by full-disk encryption (BitLocker or FileVault as applicable), and deleted when no longer needed.

Public café Wi-Fi and other untrusted networks increase risk. When remote work requires network access, users must follow the remote work and VPN requirements published by the company. Handling Restricted data on public networks without required VPN protections is prohibited.

## Access Control and Least Privilege

Access to systems must be granted on a least-privilege basis and reviewed upon role change. Within 24 hours of account creation for email, VPN, source control, and cloud admin consoles, MFA must be active as stated above. Admin privileges for cloud consoles are limited to authorized personnel and are subject to enhanced monitoring.

Upon termination or role change that removes need-to-know, managers must submit access removal requests according to IT offboarding procedures. Users must not retain access they no longer need. Sharing accounts to avoid provisioning delays is prohibited.

## Monitoring, Audit, and Enforcement

Meridian Software Inc. monitors systems and networks for security purposes to the extent permitted by law and company notice practices. Users should have no expectation of privacy in company systems beyond what applicable law requires. The Security Team and Internal Audit may verify compliance with password length and complexity, 90-day rotation, last-12 password reuse prohibition, MFA coverage, encryption status, screen-lock settings, USB exceptions, training completion within 30 days of hire and every 12 months, and phishing remediation within 5 business days.

Violations may result in corrective action up to and including termination of employment or contract, and may include referral for legal action when warranted. Good-faith mistakes that are promptly reported are generally treated more constructively than concealment.

## Exceptions

Only the Security Team may grant exceptions to this policy, and exceptions must be documented with scope, compensating controls, owner, and expiration. Business inconvenience alone is not sufficient grounds for an exception. USB storage of Confidential or Restricted data is an example of a control that requires an explicit Security Team exception before use.

Exceptions related to password length, MFA, encryption, or incident reporting timelines will be rare and tightly time-bounded. The CISO may revoke exceptions when risk changes.

## Policy Ownership

The Chief Information Security Officer (CISO) is the policy owner. The CISO or a designee will review this policy at least annually and after material incidents or material changes in Meridian Software Inc.’s technology stack. Related standards and procedures may be updated more frequently without changing the core obligations in this policy, provided they remain consistent with these requirements.

Contact channels:

- Security incidents and device loss: security@meridian-software.example
- IT Service Desk: for provisioning, encryption support, MFA enrollment, and device actions
- Policy interpretation and exception requests: Security Team under CISO governance

Workforce members using @meridian-software.example accounts are expected to read this policy, complete required training within 30 days of hire and every 12 months thereafter, and ask questions before taking actions that could expose Meridian Software Inc. or its customers to unnecessary risk.

## Operational Scenarios and Expected Behavior

To make expectations concrete, Meridian Software Inc. requires the following behaviors in common situations. If a user is prompted to create a password for a new cloud admin console, the password must be at least 14 characters and must include upper, lower, number, and symbol characters; MFA must be completed within 24 hours of account creation; and the password must be rotated within 90 days without matching any of the last 12 passwords. If a user receives a laptop rebuild, BitLocker or FileVault must be enabled before the device is used for Confidential or Restricted work, and screen lock must enforce a 5-minute inactivity timeout.

If a phone used for MFA and email is missing after a commute, the user must email security@meridian-software.example and contact IT Service Desk within 1 hour, even if the user hopes the device will reappear. If a user clicks a suspicious link and enters credentials, the user must report a suspected security incident within 4 hours, reset credentials through approved channels, and preserve evidence. If a phishing simulation failure notice arrives, remediating training must be finished within 5 business days.

These scenarios are not exhaustive. When uncertain, users should choose the more protective option and contact the Security Team. Convenience never outranks protection of Meridian Software Inc. systems and data.
