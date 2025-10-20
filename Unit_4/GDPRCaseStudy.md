# GDPR Case Study – Unencrypted USB Device Lost in Transit

## Overview

The Data Protection Commission (DPC) case *“Unencrypted USB device lost in the post”* concerns a private-sector controller that mailed consent forms and an **unencrypted USB device containing pictures of minors**. During transit the package was damaged, the USB fell out and was lost.  
This case highlights the GDPR’s **integrity and confidentiality principle (Art. 5(1)(f))** and the duty to implement **appropriate technical and organisational measures (Art. 32)**. Article 32(1) explicitly lists *“pseudonymisation and encryption of personal data”* as examples of required safeguards.  
Because the loss constituted a **personal-data breach**, Article 33 (breach notification) also applied.

---

## Resolution

The DPC concluded that the breach *“could have been prevented or mitigated”* had the controller encrypted the data and used secure shipping (e.g. registered post or courier).  
The controller adopted the DPC’s recommendations—encrypting all portable media and changing mailing procedures—and the case was closed without a fine. The resolution therefore emphasised **guidance and remediation over sanction**.

---

## Recommended Controls (Information Security Manager Perspective)

| Control Area | Recommended Action | Rationale / Reference |
|---------------|--------------------|------------------------|
| **Encryption** | Enforce full-disk or file-level encryption (e.g. BitLocker) for all portable media. | GDPR Art. 32 (1); ensures unreadable data if lost. |
| **Secure Transport** | Prohibit standard mail for sensitive data; use registered post, encrypted email, or secure couriers. | DPC guidance on safe transfer methods. |
| **Data-Handling Policy** | Define policies restricting removal of unencrypted data; document and review under ISO 27001 A.8 (Asset Management). | Aligns with ISO 27002 control 8.3.3 on removable media. |
| **Training & Awareness** | Conduct regular staff training on data protection and secure handling. | ISO 27001 A.7 (Human Resource Security). |
| **Incident Response / DPIA** | Maintain a breach-response plan (GDPR Art. 33) and perform Data Protection Impact Assessments for data-transfer processes. | Proactive risk identification and accountability. |

Implementing these measures reduces recurrence probability and demonstrates compliance with **GDPR Art. 5, Art. 32, and Art. 33**, as well as ISO 27001 best practice.

---

## References (Harvard Cite Them Right)

- Data Protection Commission (2018) *Case study: Unencrypted USB device lost in the post*. Available at: [https://www.dataprotection.ie/](https://www.dataprotection.ie/)  
- GDPR Info (2024) *Article 32 – Security of processing*. Available at: [https://gdpr-info.eu/art-32-gdpr/](https://gdpr-info.eu/art-32-gdpr/)  
- ISO (2013) *ISO/IEC 27001:2013 – Information security management systems – Requirements*. Geneva: ISO.  
- NovelVista (2024) *ISO 27001 controls for removable media and data in transit*. Available at: [https://www.novelvista.com/](https://www.novelvista.com/)
