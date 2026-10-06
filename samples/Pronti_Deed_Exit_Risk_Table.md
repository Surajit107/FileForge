# Pronti Deed of Exit — Clause-by-Clause Risk Table

| Clause number | Risk | Why risky |
|---|---|---|
| Background A | 🟢 Low | Confirms the consultant provided DevOps, cloud, deployment and technical support services as an independent contractor. Mostly factual. |
| Background B | 🔴 Critical | Says all Services have already been paid. If any invoice, fee, reimbursement or other amount is still unpaid, signing this creates a serious problem for recovering it later. |
| Background C | 🟡 Medium | Fixes 1 October 2026 as the Separation Date and says the engagement ended by agreement. This can affect notice-period or termination-payment claims. |
| Background D | 🟠 High | Confirms the consultant had access to sensitive infrastructure, credentials, IP addresses, Cloudflare, cloud accounts, API keys and secrets. This supports later security/confidentiality claims against the consultant. |
| Background E | 🟠 High | Makes the Experience Letter part of the bargain for accepting the deed's obligations. The letter is being used as leverage to obtain the consultant's promises. |
| Prior Arrangements definition | 🔴 Critical | Covers previous agreements, drafts, offers, emails, messages and oral arrangements, whether signed or not. The deed is designed to replace earlier understandings. |
| Commencement Date definition | 🟡 Medium | Several obligations are made retrospective to the first day of Services, so the exact commencement date matters. |
| Company Materials definition | 🔴 Critical | Extremely broad. Includes code, data, backups, documentation, credentials, configurations, infrastructure information, devices and other Company property. |
| Company Systems definition | 🔴 Critical | Covers almost the entire technical environment: servers, cloud, databases, repositories, CI/CD, DNS, CDN, Cloudflare, domains, monitoring and third-party services. Missing one can create handover risk. |
| Competing Business definition | 🔴 Critical | Very broad competitor definition. It can cover businesses developing substantially similar delivery/logistics/technology platforms and can extend to countries where the Company operates or plans to operate. |
| Confidential Information definition | 🔴 Critical | Covers information whether or not marked confidential, including business, customer, infrastructure, architecture, algorithms, pricing, strategy and the deed itself. |
| Credentials definition | 🔴 Critical | Includes passwords, API keys, secrets, tokens, certificates, SSH keys, signing keys, recovery codes and 2FA. Forgotten credentials can create breach exposure. |
| Harmful Act definition | 🟡 Medium | Imports the prohibited acts from clause 7.1 into later warranties and obligations. |
| Infrastructure Information definition | 🔴 Critical | Covers current and historical IPs, network topology, firewall/WAF/Cloudflare configuration, hosting, architecture, deployment procedures, security controls and vulnerabilities. |
| Intellectual Property Rights definition | 🟠 High | Extremely broad worldwide definition covering software, code, inventions, patents, designs, databases, trade secrets, know-how and similar rights. |
| Personal Information definition | 🟠 High | Uses both Australian and Indian privacy-law concepts, potentially creating obligations across both jurisdictions. |
| Related Entity definition | 🔴 Critical | Extends protection to related bodies and entities controlled by Company directors that operate/support the Pronti platform. |
| Restraint Period definition | 🔴 Critical | Establishes a 12-month period after separation for the restrictive covenants. |
| Third Party definition | 🟠 High | Covers anyone other than the consultant who performed Services or obtained access through the consultant. Important because clause 10.6 makes the consultant responsible for Third Party conduct. |
| Work Product definition | 🔴 Critical | Covers code, scripts, infrastructure-as-code, pipelines, documentation, designs, data, inventions, improvements and other work created/contributed to in connection with Services, including incomplete work. |
| 1.2 | 🟠 High | "Including" is expressly non-limiting and the deed says no interpretation rule applies against the Company because it prepared the deed. This supports a broad interpretation. |
| 2.1 | 🔴 Critical | Makes the deed standalone. The consultant's obligations do not depend on whether an earlier agreement was valid or enforceable. |
| 2.2 | 🔴 Critical | Says clauses 6–9 apply from the Commencement Date, including retrospectively where they did not previously bind the consultant. |
| 2.3 | 🔴 Critical | Replaces all Prior Arrangements and says the consultant has no rights under them, while Company protections from prior arrangements may be preserved. Strongly one-sided. |
| 2.4 | 🟠 High | Says the engagement ended by mutual agreement and no notice period, payment in lieu or other termination amount applies. |
| 2.5 | 🔴 Critical | Consultant confirms they were always an independent contractor and gives up potential salary, leave, gratuity, PF, superannuation, bonus, equity and other employment-related entitlements. |
| 3.1 | 🔴 Critical | Requires return of all Company Materials within 48 hours and permanent deletion from devices, email, messaging apps, cloud storage, password managers and authenticators. Very difficult to guarantee across backups and old devices. |
| 3.2 | 🔴 Critical | Specifically includes database dumps, backups, exports, .env files, SSH keys, screenshots, notes and credential/infrastructure records. Accidental retention can become a breach. |
| 3.3 | 🔴 Critical | Requires a notarised affidavit or approved certification confirming no Company Materials remain and making several factual declarations. |
| 3.3(a) | 🔴 Critical | Requires confirmation that no Company Materials are retained anywhere. A forgotten backup or file can make the certification inaccurate. |
| 3.3(b) | 🔴 Critical | Requires confirmation that all Company accounts and credentials were removed from password managers/authenticators. |
| 3.3(c) | 🔴 Critical | Requires identifying every copy, export or download of Company data made during the engagement. This is extremely broad and difficult to establish from memory. |
| 3.3(d) | 🔴 Critical | Requires confirmation that no Company Materials, credentials or infrastructure information were disclosed to anyone. Any historical sharing must be accurately disclosed. |
| 3.3(e) | 🔴 Critical | Requires confirmation that no Third Party accessed Company systems/materials through the consultant except as disclosed in Schedule 1. |
| 3.3(f) | 🔴 Critical | Requires confirmation that Schedule 1 is complete and accurate. This makes the technical inventory a contractual warranty. |
| 3.4 | 🔴 Critical | If the Company reasonably suspects retention, access or disclosure, it can require forensic inspection of devices, accounts or storage used for Services. If a breach is found, consultant pays examiner costs. This can affect personal devices/accounts. |
| 3.5 | 🟠 High | If Company Materials are discovered later, consultant must notify within 24 hours and follow Company instructions. Short deadline and ongoing obligation. |
| 3.6 | 🔴 Critical | Confirms all Work Product is in Company repositories/systems and none exists in personal repositories/accounts/systems. A forgotten private/local copy creates risk. |
| 4.1 | 🔴 Critical | Requires a complete list within 48 hours of every Company System administered or credential held, every sole-admin account and every known credential. |
| 4.2 | 🔴 Critical | Requires transfer of ownership/super-admin rights for Cloudflare, cloud accounts, domain registrar, repositories, app stores and other systems. |
| 4.3 | 🟡 Medium | Requires replacement of personal email, phone or authenticator used for Company access. Reasonable, but obtain written confirmation that personal recovery methods are removed. |
| 4.4 | 🟠 High | Requires documentation of deployment, release, backup, monitoring, incident procedures and work in progress plus handover sessions. No separate payment is stated for this post-exit work. |
| 4.5 | 🔴 Critical | Prohibits changing/deleting/disabling/reconfiguring systems, credentials, DNS, firewall or Cloudflare except on written instruction. Verbal instructions create evidence problems. |
| 5.1 | 🔴 Critical | No access to Company Systems after Separation Date except written authorization for handover. Even an innocent login/check can become unauthorized access. |
| 5.2 | 🔴 Critical | Explicitly characterizes unauthorized access as potentially falling under Indian IT law, including sections 43 and 66, and equivalent laws elsewhere. |
| 5.3 | 🟡 Medium | Company can change credentials, IPs and configurations without notifying the consultant. |
| 6.1 | 🔴 Critical | Requires strict confidentiality and prohibits use, disclosure, publication, sale or sharing of Confidential Information for any purpose. |
| 6.2 | 🔴 Critical | Specifically prohibits disclosure of infrastructure information and credentials, including online posting or giving them to someone who could use them. |
| 6.3 | 🟠 High | If legally compelled to disclose information, consultant must notify Company first where lawful and cooperate with protective measures. |
| 6.4 | 🔴 Critical | Confidentiality obligations continue without any time limit. |
| 7.1(a) | 🔴 Critical | Permanently prohibits denial-of-service, flooding, traffic/load attacks and other disruptive acts. Breach is subject to the deed's strong remedies. |
| 7.1(b) | 🔴 Critical | Prohibits accessing, scanning, probing or testing Company systems/IPs. Even security testing should not be done without written authorization. |
| 7.1(c) | 🔴 Critical | Prohibits malicious code, backdoors, hidden processes, unauthorized users, scheduled tasks and remote access mechanisms. |
| 7.1(d) | 🔴 Critical | Prohibits deleting, altering, encrypting, corrupting, withholding or exfiltrating Company data, code, backups or configurations. |
| 7.1(e) | 🔴 Critical | Prohibits changing, disabling or misdirecting DNS, Cloudflare, firewall, security or monitoring settings. |
| 7.1(f) | 🔴 Critical | Prohibits bypassing or circumventing security measures. |
| 7.2 | 🔴 Critical | Consultant confirms these prohibited acts never occurred and confirms no undisclosed access mechanism, account, key, scheduled task or code was left behind. Historical warranty. |
| 7.3 | 🟠 High | Requires immediate written notification of actual/threatened harmful acts or credential/infrastructure disclosure. |
| 8.1 | 🔴 Critical | Says all Work Product and related IP belong to Company absolutely from creation. |
| 8.2 | 🔴 Critical | Irrevocably assigns existing and future Work Product/IP to Company. |
| 8.3(a) | 🔴 Critical | Defines assigned works broadly, including code, scripts, configurations and documentation in Company repositories/systems. |
| 8.3(b) | 🔴 Critical | Assigns all rights in all media and forms now known or developed in future. |
| 8.3(c) | 🔴 Critical | Assignment lasts for the full copyright term plus renewals/extensions. |
| 8.3(d) | 🔴 Critical | Assignment is worldwide. |
| 8.3(e) | 🔴 Critical | Assignment will not lapse or revert merely because Company does not exercise a right. |
| 8.4 | 🔴 Critical | Background IP receives a perpetual, irrevocable, worldwide, royalty-free, transferable and sublicensable licence if incorporated into or needed to use/maintain/modify Work Product. Important for reusable personal tools/templates. |
| 8.5 | 🟠 High | Waives moral/author rights as far as legally permitted and permits modification/publication without attribution. |
| 8.6 | 🔴 Critical | Consultant warrants no Work Product was assigned/licensed elsewhere and no Work Product infringes third-party rights. |
| 8.7(a) | 🔴 Critical | Warrants no malicious code, backdoor, undisclosed account or remote access mechanism was introduced. |
| 8.7(b) | 🔴 Critical | Warrants no open-source/third-party code or confidential information was included on terms restricting Company's ownership/use/modification/commercial exploitation. This should be checked against dependencies. |
| 8.7(c) | 🔴 Critical | Warrants no subcontracting or access sharing except what Schedule 1 discloses. |
| 8.7(d) | 🟠 High | Warrants compliance with all applicable laws, including anti-bribery and anti-corruption laws. Broad legal warranty. |
| 8.8 | 🔴 Critical | Prohibits using Work Product or Company Materials to build, assist or advise another product/business. Needs distinction between Company-specific material and general skills/knowledge. |
| 8.9 | 🔴 Critical | Requires future IP cooperation without further payment and gives Company/directors a claimed power of attorney to sign documents in consultant's name if consultant fails to act within 7 days. Major legal risk. |
| 9.1 | 🔴 Critical | Consultant confirms holding no Company personal information. If any local DB, dump, log, export, screenshot or backup contains personal data, this statement may be false. |
| 9.2 | 🔴 Critical | Requires conduct that does not cause Company to breach Australian/Indian privacy and related laws. Broad compliance obligation. |
| 10.1 opening | 🔴 Critical | 12-month restrictions apply across employment, contracting, consulting, advising, partnership, shareholding and other involvement. |
| 10.1(a) | 🟠 High | Cannot solicit/encourage Company employees, contractors or development team members to leave or reduce their engagement. |
| 10.1(b) | 🟠 High | Cannot solicit/entice away retailers, customers, drivers, suppliers or partners or encourage them to reduce dealings with Company. |
| 10.1(c) | 🔴 Critical | Cannot build/contribute to a platform that replicates or is substantially derived from Company's architecture, infrastructure, features, algorithms or workflows. Can affect future work in similar products. |
| 10.1(d) | 🔴 Critical | Cannot provide DevOps, infrastructure, engineering or technical services to a Competing Business for 12 months. Direct future-employment restriction. |
| 10.2 | 🔴 Critical | Before joining a Competing Business, consultant must disclose the business/role to Company and give the new business copies of key restrictions. Company may notify the new business itself. |
| 10.3 | 🔴 Critical | Broad non-disparagement restriction covering LinkedIn, social media, GitHub, forums, review sites, employer-rating sites and press. It is not expressly limited to false statements. |
| 10.4 | 🟠 High | Cannot use Company name, logo, trademarks or Work Product in portfolio/case study/publicity without written consent. CV/profile/interview use is limited to a general role description. |
| 10.5 | 🟠 High | For 30 days, consultant must respond within 2 business days to reasonable/limited handover questions. No separate payment is stated. |
| 10.6 | 🔴 Critical | If a Third Party accessed systems through consultant, consultant must obtain an equivalent undertaking if requested and is liable for that Third Party's acts/omissions as if they were the consultant's own. |
| 10.7 | 🔴 Critical | Consultant acknowledges the restraints are reasonable and necessary and that each is separate/severable. This is drafted to strengthen Company's position if a restriction is challenged. |
| 11.1 | 🔴 Critical | Experience Letter is conditional on signed deed, completed handover and Certification. |
| 11.2 | 🔴 Critical | Company need not issue the Experience Letter if consultant breaches before it is issued. |
| 11.3 | 🟠 High | Company agrees to verify engagement consistently with the Experience Letter unless withdrawn. Useful protection, but conditional. |
| 11.4 | 🔴 Critical | Company can withdraw the Experience Letter for material breach of clauses 3–10 or false/misleading Schedule 1/Certification and can tell verification requests that it was withdrawn. |
| 11.5 | 🔴 Critical | Experience Letter, non-disparagement promise and AUD 10 are stated to be consideration for the deed and IP assignment. The deed also says it binds as a deed regardless of consideration. |
| 11.6 | 🔴 Critical | Consultant confirms all fees/amounts are paid and promises not to submit further invoices or claim further compensation/benefits. Do not sign this if anything is outstanding. |
| 11.7 | 🔴 Critical | Broad release of Company, Related Entities, directors, officers and personnel from known/unknown claims relating to Services, prior arrangements, engagement or its end, including fees, employment entitlements and IP claims. |
| 11.8 | 🔴 Critical | Consultant warrants Schedule 1 and Certification are true, complete and not misleading. Company says it relies on this warranty. |
| 12.1 | 🔴 Critical | Company can seek injunctions, specific performance and other equitable remedies without proving actual damage, plus damages and costs. Gives Company strong legal leverage. |
| 12.2 | 🔴 Critical | Broad indemnity for all loss, damage, costs and liability, including full legal costs, forensic investigation, incident response, credential rotation, infrastructure changes, restoration and notifications. |
| 12.3 | 🔴 Critical | Consultant liability is expressly **not capped**. There is no maximum financial exposure. |
| 12.4 | 🔴 Critical | Company's total liability to consultant is limited to issuing the Experience Letter. This is highly asymmetric against the consultant. |
| 12.5 | 🟠 High | Company can set off amounts the consultant owes against amounts Company owes the consultant. Important if any payment remains outstanding. |
| 12.6 | 🟠 High | Company retains the right to report suspected offences to law enforcement in India, Australia or elsewhere. |
| 13.1 | 🔴 Critical | Indian law governs, but Company can also bring proceedings in other competent courts including NSW Australia. This creates cross-border litigation exposure. |
| 13.2 | 🟡 Medium | If a provision is unenforceable, it can be narrowed/severed while the rest continues. One failed clause does not necessarily invalidate the deed. |
| 13.3 | 🔴 Critical | Says amendments need writing signed by the **Company**. It does not expressly require the consultant's signature. This is asymmetric and should be changed to require both parties. |
| 13.4 | 🔴 Critical | Clauses 2 and 5–14 survive indefinitely except the 12-month restraint in 10.1. Many obligations therefore continue after handover permanently. |
| 13.5 | 🟢 Low | Sets email as a valid method for notices. Mainly administrative. |
| 13.6 | 🟡 Medium | Company can arrange stamping in India and consultant must sign documents reasonably required for it. Additional post-signing cooperation obligation. |
| 13.7 | 🟠 High | Deed binds heirs/legal representatives; consultant cannot assign rights while Company can assign rights to Related Entities or a purchaser. Asymmetric. |
| 14.1 | 🔴 Critical | Consultant becomes bound when they sign, witness and deliver the deed, even if Company has not signed it. Do not assume countersignature is required. |
| 14.2 | 🔴 Critical | Consultant confirms they understand English, read/understood the deed, had an opportunity for independent legal advice and signed voluntarily. This makes later claims of misunderstanding harder. |
| Execution — Company | 🟡 Medium | Company execution must comply with the stated Corporations Act execution method. Check that the execution block is correctly completed. |
| Execution — Consultant | 🔴 Critical | Consultant must execute as a deed in front of witnesses. Witnessing/delivery formalities matter because the document relies on deed status. |
| Schedule 1 — General | 🔴 Critical | Must be completed within 48 hours and is later warranted to be complete and accurate. This is a technical completeness declaration. |
| Schedule 1 — Cloudflare | 🔴 Critical | All Cloudflare account/admin/recovery/transfer information must be identified. Missing access can create handover and warranty problems. |
| Schedule 1 — Cloud hosting | 🔴 Critical | AWS/GCP/other cloud accounts and relevant admin access must be identified. |
| Schedule 1 — Servers and SSH | 🔴 Critical | Every server and SSH access path must be accounted for without putting private keys/passwords into the schedule. |
| Schedule 1 — Databases | 🔴 Critical | Databases, admin access, exports/backups and personal copies need to be considered because of clauses 3 and 9. |
| Schedule 1 — Domain/DNS | 🔴 Critical | Every domain registrar/DNS access path needs to be identified and transferred. |
| Schedule 1 — Code repositories | 🔴 Critical | Every repository/account containing Company Work Product must be identified. Personal repositories are particularly important because 3.6 says none contains Work Product. |
| Schedule 1 — CI/CD and secrets | 🔴 Critical | Deployment pipelines, secret stores and service access must be identified. Forgotten service credentials can become a serious breach issue. |
| Schedule 1 — Apple/Google developer accounts | 🟠 High | App-store ownership/admin access must be identified if applicable. |
| Schedule 1 — Firebase/push notifications | 🟠 High | Firebase projects, service accounts and notification infrastructure should be accounted for if applicable. |
| Schedule 1 — Third-party APIs | 🔴 Critical | Payment, maps, SMS, email and other API accounts must be listed without exposing actual secrets in the document. |
| Schedule 1 — Monitoring/logging/alerts | 🔴 Critical | Monitoring and logging systems plus admin/service access must be accounted for. |
| Schedule 1 — Scheduled jobs/cron/service accounts | 🔴 Critical | Easy to forget and particularly important because clause 7.2 requires confirmation that no undisclosed scheduled task/access mechanism remains. |
| Schedule 1 — Third Parties given access | 🔴 Critical | Every person/vendor/freelancer who received access must be disclosed. Clause 10.6 can make the consultant liable for their conduct. |
| Schedule 1 — Other | 🔴 Critical | Catch-all category means the consultant should not assume only the listed systems matter. |
| Schedule 1 — Declaration | 🔴 Critical | Consultant confirms the Schedule contains every system, account, access mechanism, scheduled task, service account and Third Party they created/administered/held credentials for/gave access to. This is a broad contractual warranty. |

---

## Most Serious Risks

| Clause | Risk | Why risky |
|---|---|---|
| 12.2 | 🔴 Critical | Broad, potentially unlimited indemnity covering legal, forensic, security, infrastructure and notification costs. |
| 12.3 | 🔴 Critical | Explicitly removes any liability cap for the consultant. |
| 12.4 | 🔴 Critical | Company's liability is heavily limited compared with the consultant's uncapped liability. |
| 11.7 | 🔴 Critical | Broad release can eliminate claims against Company relating to the engagement. |
| 11.6 | 🔴 Critical | Confirms everything has been paid and no further invoice/claim exists. |
| 10.1(d) | 🔴 Critical | 12-month restriction on providing technical services to a Competing Business. |
| 10.2 | 🔴 Critical | Requires disclosure of future competing employment and permits Company to notify the new employer. |
| 3.4 | 🔴 Critical | Allows forensic examination of devices/accounts if Company reasonably suspects retention/access/disclosure. |
| 8.4 | 🔴 Critical | Gives Company a perpetual, worldwide, royalty-free licence over incorporated Background IP. |
| 8.9 | 🔴 Critical | Gives Company/directors a claimed power of attorney for IP paperwork if consultant does not cooperate. |
| 10.3 | 🔴 Critical | Broad non-disparagement restriction covering public professional/social platforms and review sites. |
| 13.3 | 🔴 Critical | Amendment wording is Company-only rather than clearly requiring both parties. |
| 13.4 | 🔴 Critical | Most obligations survive indefinitely. |
