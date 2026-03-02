# Falcon Platform UAT Plan

## Overview
Comprehensive UAT testing for Falcon AI Recruiter platform based on existing bug tracker.

## Credentials
| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@example.com | admin123 |
| **Client** | ahmed.hassan@techcorp.ae | SecurePass123! |
| **Candidate** | interviewee@example.com | interviewee123 |

## Bug Status Summary (from tracker)

### By Status
- 🔴 **Open Bugs**: 78
- ✅ **Closed Bugs**: 28
- **Total**: 106 bugs tracked

### By Priority
- **Critical**: 2 (both closed)
- **High**: 35 (mix of open/closed)
- **Medium**: 42
- **Low**: 27

### By Category
- **Code**: 25 bugs
- **UI/UX**: 52 bugs
- **Flow/Process**: 18 bugs
- **Text/Content**: 11 bugs

---

## UAT Test Plan

### Phase 1: Landing Page (Public)
**Test as: Anonymous User**

| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| LP-01 | LP-01 | "Start Free Trial" CTA redirects correctly | Should go to registration, not login |
| LP-02 | LP-02 | Favicon displays | Should show Falcon brand icon |
| LP-03 | LP-03 | Stats emoji renders | 95% Match Accuracy should show correct icon |
| LP-04 | LP-04 | "Watch Demo" button works | Should play video or open modal |
| LP-05 | LP-05 | "See it in action" links work | Should navigate to feature pages |
| LP-06 | LP-06 | Testimonials show real data | Should show names/photos, not initials |
| LP-07 | LP-07 | "Request Demo" button works | Should open form or navigate |

### Phase 2: Client User (Employer)
**Test as: ahmed.hassan@techcorp.ae**

#### Dashboard
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-01 | CL-01 | Candidates stat matches interviews | Should show >0 candidates |
| CL-02 | CL-02 | "Create Job" card navigates correctly | Should go to job creation |
| CL-03 | CL-03 | Stats remain consistent | Should not change on interaction |
| CL-50 | CL-50 | Statistics show correct totals | Should show actual counts |

#### Jobs
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-04 | CL-04 | Jobs page shows active jobs | Should display 3+ jobs |
| CL-17 | CL-17 | Jobs load consistently | Should not show 0 on refresh |
| CL-18 | CL-18 | Job cards show proper description | Should not show raw CV text |
| CL-19 | CL-19 | Job titles are proper | Should not show 'asdf' placeholders |
| CL-20 | CL-20 | Status badge formatting | Should show 'Published' not 'published' |
| CL-21 | CL-21 | Job detail shows all fields | Should match creation data |
| CL-55 | CL-55 | Seniority Level saves correctly | Frontend/backend values match |
| CL-56 | CL-56 | Status change confirmation | Should show confirmation dialog |

#### Job Creation Wizard
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-09 | CL-09 | "Generate with AI" works | Should populate job description |
| CL-10 | CL-10 | Step 2 labeling | Should match content |
| CL-11 | CL-11 | Seniority Level visibility | Should not disappear |
| CL-12 | CL-12 | Location field in Step 3 | Should be present |
| CL-13 | CL-13 | Engagement Length options | Should have meaningful options |
| CL-14 | CL-14 | Location placement | Should be in Step 3 not 4 |
| CL-15 | CL-15 | Success modal positioning | Should not overlap form |

#### Candidates
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-08 | CL-08 | Candidates page shows data | Should show candidates |
| CL-35 | CL-35 | Candidates with interviews | Should show >0 candidates |
| CL-57 | CL-57 | Search accuracy | Should not show false positives |
| CL-58 | CL-58 | Bulk actions | Checkboxes should work with toolbar |

#### Interviews
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-06 | CL-06 | Interviews load | Should not show skeleton indefinitely |
| CL-28 | CL-28 | Checklist and Date columns | Should show actual data |
| CL-30 | CL-30 | Pagination | Should have pagination |
| CL-33 | CL-33 | Interview detail dates | Should show scheduled/completed dates |
| CL-34 | CL-34 | AI summary availability | Should show if interview completed |
| CL-61 | CL-61 | Reschedule option | Should be able to reschedule |
| CL-62 | CL-62 | Pagination on interviews | Should not show all at once |
| CL-63 | CL-63 | Reminder system | Should have notifications |

#### Pipeline
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-27 | CL-27 | Sidebar Pipeline link | Should go to Pipeline not Interviews |
| CL-59 | CL-59 | Drag-and-drop | Should support Kanban drag-and-drop |

#### Analytics
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-36 | CL-36 | Analytics shows data | Should not show 0% for all metrics |
| CL-37 | CL-37 | Source Effectiveness | Should not show 'unknown' |
| CL-38 | CL-38 | Interviewed percentage | Should calculate correctly |
| CL-39 | CL-39 | Score Analytics | Should show total scores |

#### Assessments
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-45 | CL-45 | Question title typo | Should not show 'Createt Sum funation' |
| CL-46 | CL-46 | Expired assessment button | Should not show 'Continue' for expired |
| CL-47 | CL-47 | Create Assessment button | Should be present |

#### Navigation
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CL-05 | CL-05 | Sidebar navigation | Should go to correct pages |
| CL-07 | CL-07 | Sidebar offset | Links should match destinations |
| CL-49 | CL-49 | User Menu | Should have Profile, Settings, etc. |
| CL-53 | CL-53 | Templates link | Should go to correct page |

### Phase 3: Admin User
**Test as: admin@example.com**

#### Dashboard
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-01 | AD-01 | Statistics show data | Should not show 0 across all |
| AD-02 | AD-02 | Getting Started checklist | Should show correct progress |
| AD-28 | AD-28 | Checklist completion | Should update correctly |

#### Jobs
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-04 | AD-04 | Active Jobs count | Should match platform data |
| AD-11 | AD-11 | Jobs page shows jobs | Should not show 0 |
| AD-42 | AD-42 | Jobs count consistency | Should match Client Accounts |

#### Candidates
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-12 | AD-12 | Candidates show | Should not show 0 |

#### Interviews
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-13 | AD-13 | Interviews show | Should not show 'No interviews yet' |
| AD-45 | AD-45 | Empty state message | Should show admin-facing message |

#### Client Accounts
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-35 | AD-35 | Client count display | Should show correct number |
| AD-36 | AD-36 | Client card info | Should not duplicate name |
| AD-37 | AD-37 | Job count consistency | Should match client view |
| AD-38 | AD-38 | Placeholder data | Should not show test data |
| AD-39 | AD-39 | Add Client button | Should be present |
| AD-43 | AD-43 | Companies count | Should match Client Accounts |

#### Analytics
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-15 | AD-15 | Analytics loads | Should not be stuck loading |
| AD-16 | AD-16 | KPIs show data | Should not show 0 |

#### Management
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-08 | AD-08 | Clients link | Should go to correct page |
| AD-09 | AD-09 | Users page | Should not crash |
| AD-10 | AD-10 | Enterprise link | Should navigate |
| AD-40 | AD-40 | Users page stability | Should not crash app |

#### Tools & Config
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-17 | AD-17 | Templates link | Should go to correct page |
| AD-19 | AD-19 | Eval Policies link | Should navigate correctly |
| AD-21 | AD-21 | Eval Policies vs Feedback | Should go to different pages |
| AD-22 | AD-22 | Evidence-Based Scoring | Should have browse/selection |
| AD-23 | AD-23 | Integrations page | Should load content |
| AD-25 | AD-25 | Create Rule button | Should go to correct page |
| AD-32 | AD-32 | ATS Settings label | Should match page title |
| AD-34 | AD-34 | Admin Panel link | Should go to correct page |

#### Role Spec
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-18 | AD-18 | Placeholder data | Should not show 'asdf' |
| AD-44 | AD-44 | Activity log | Should show recent activities |

#### User Menu
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| AD-41 | AD-41 | User Menu items | Should have Profile, Settings, etc. |

### Phase 4: Candidate User
**Test as: interviewee@example.com**

#### Dashboard
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-01 | CA-01 | Default landing page | Should be appropriate for candidate |
| CA-04 | CA-04 | Greeting message | Should show actual name not 'Interview!' |
| CA-05 | CA-05 | Dashboard content | Should have meaningful stats |
| CA-06 | CA-06 | Getting Started | Should have onboarding guide |

#### My Interviews
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-02 | CA-02 | Search placeholder | Should say 'Search interviews' |
| CA-03 | CA-03 | Interviews display | Should show scheduled interviews |

#### My Application
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-07 | CA-07 | Application loads | Should not show error |
| CA-08 | CA-08 | Error guidance | Should have helpful CTA if error |

#### Assessments
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-10 | CA-10 | Search placeholder | Should say 'Search assessments' |

#### AI Assistant
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-12 | CA-12 | Prompt suggestions | Should be candidate-focused |
| CA-13 | CA-13 | Input placeholder | Should be candidate-appropriate |
| CL-48 | CL-48 | Platform questions | Should answer candidate questions |

#### Help Center
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-14 | CA-14 | Content focus | Should be candidate-focused |
| CA-15 | CA-15 | Quick links | Should be candidate-relevant |
| HC-01 | HC-01 | FAQ expansion | All FAQs should expand |

#### Navigation
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| CA-16 | CA-16 | User Menu | Should have Profile, Settings |
| CA-17 | CA-17 | Role label | Should show 'Candidate' not 'Interviewee' |
| CA-20 | CA-20 | Search placeholder | Should be candidate-appropriate |

### Phase 5: Help Center (All Roles)
| Test ID | Bug ID | Description | Status to Verify |
|---------|--------|-------------|------------------|
| HC-01 | HC-01 | FAQ expansion | All items should expand |
| CL-64 | CL-64 | Click target | Should be on text, not just chevron |

---

## User Journey Documentation

For each role, I will document:
1. **Login flow** - Steps to access platform
2. **Main dashboard** - Key features and navigation
3. **Core workflows** - Primary tasks for each role
4. **Common actions** - Frequently used features

---

## Deliverables

1. **UAT Report** - Pass/fail status for each test
2. **Bug Verification** - Which tracked bugs are fixed/not fixed
3. **New Issues** - Any new bugs discovered
4. **User Journey Docs** - Training documentation for each role
