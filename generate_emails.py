import random
import csv

names = [
    "Sarah", "James", "Priya", "Michael", "Aisha",
    "David", "Emma", "Jay", "Ashish", "Danny",
    "Olivia", "Leonard", "May", "Lucas", "Janie",
    "Noah", "Layla", "Ethan", "Sofia", "Arjun",
    "Grace", "Thomas", "Nadia", "Ryan", "Mavi",
    "Rohan", "Charlotte", "Vikram", "Raj", "Aditya",
    "Mark", "Karan", "Penny", "Nikhil", "Florence",
    "Ishaan", "Amelia", "Rahul", "Isla", "Varun",
    "Daisy", "Siddharth", "Tom", "Ananya", "George",
    "Kavya", "Oliver", "Meera", "Henry", "Divya"
]
courses = [
    "Python for Data Science", "Introduction to Machine Learning", "Cybersecurity Fundamentals",
    "Digital Marketing Basics", "Financial Accounting", "Introduction to Psychology",
    "Web Development with JavaScript", "Project Management Essentials", "Data Analysis with Excel",
    "Public Speaking Skills", "Introduction to Artificial Intelligence", "Graphic Design Principles",
    "Business Strategy Fundamentals", "Cloud Computing Basics", "Statistics for Beginners",
    "UX Design Foundations", "Introduction to SQL", "Content Writing Essentials",
    "Negotiation Skills", "Personal Finance Management"
]

#legitimate emails
amazon_subjects = [
    "Your order has shipped",
    "Order confirmation: {order_id}",
    "Your package is on its way",
    "Delivery update for your recent order",
    "Your order is out for delivery",
    "Order {order_id} has been dispatched",
    "Your Amazon order summary",
    "Track your package: {order_id}",
    "Your order will arrive soon",
    "Thanks for your order, {name}",
    "Good news — your order is on its way",
    "Your recent purchase has been confirmed",
    "Shipping confirmation for order {order_id}",
    "Your delivery is scheduled for {date}",
    "Order update: your items are packed",
    "Your order is being prepared",
    "Dispatch confirmation: {order_id}",
    "Your parcel is on its way to you",
    "Order {order_id} is now with the courier",
    "You'll receive your order by {date}"
]

amazon_bodies = [
    "Hi {name}, your order {order_id} has shipped and is on its way. Track your package here: {link}",
    "Hello {name}, thank you for your order. Your items will arrive by {date}. View order details: {link}",
    "Hi {name}, your recent purchase is confirmed. Order total: {amount}. Track shipment: {link}",
    "Hi {name}, your order {order_id} is out for delivery and should arrive {date}. Track here: {link}",
    "Hello {name}, here is a summary of your recent order. Total charged: {amount}. View details: {link}",
    "Hi {name}, good news — your package is on schedule for delivery {date}. Track it here: {link}",
    "Hello {name}, your order {order_id} has been packed and dispatched. Expected arrival: {date}. Track: {link}",
    "Hi {name}, thanks for shopping with us. Your order total was {amount}. View your invoice: {link}",
    "Hello {name}, just a quick update — your delivery is on track for {date}. Details here: {link}",
    "Hi {name}, your order {order_id} is being prepared for delivery. Track progress here: {link}",
    "Hello {name}, we are pleased to confirm your order has been dispatched. Estimated delivery: {date}. Track: {link}",
    "Hi {name}, your parcel is now with the courier. You should receive it by {date}. Track here: {link}",
    "Hello {name}, your order of {amount} is confirmed and on its way. View full details: {link}",
    "Hi {name}, a quick heads-up that your order {order_id} leaves our warehouse today. Track: {link}",
    "Hello {name}, your recent order has been successfully processed and dispatched. Details: {link}",
    "Hi {name}, your delivery is scheduled for {date}. You can track your parcel here: {link}",
    "Hello {name}, we have confirmed your order and it is now on its way to you. Total: {amount}. Track: {link}",
    "Hi {name}, your order {order_id} is packed and ready. The courier will collect it {date}. Track: {link}",
    "Hello {name}, great news — your order has left our fulfilment centre. Estimated arrival: {date}. Details: {link}",
    "Hi {name}, your purchase of {amount} is confirmed. Your order {order_id} is now in transit. Track: {link}"
    "Hi {name}, please confirm your email address to continue receiving LinkedIn notifications: {link}",
    "Hello {name}, action required: please review and update your LinkedIn profile details: {link}",
    "Hi {name}, please verify your account to continue accessing LinkedIn premium features: {link}",
    "Hello {name}, we need you to confirm your identity to keep your LinkedIn account secure: {link}",
    "Hi {name}, please review your account settings and confirm your preferences here: {link}"
    "Hi {name}, please confirm your delivery address for order {order_id} to ensure successful delivery: {link}",
    "Hello {name}, action required: please review your recent order {order_id} and confirm the details are correct: {link}",
    "Hi {name}, please update your payment method to complete your pending order of {amount}: {link}",
    "Hello {name}, we need you to confirm your order {order_id} before we can dispatch your items: {link}",
    "Hi {name}, please verify your delivery address for your upcoming order. Confirm here to avoid delays: {link}"
]

linkedin_subjects = [
    "{name} viewed your profile",
    "You have a new connection request",
    "Your weekly LinkedIn digest",
    "New message from {name}",
    "Someone is looking at your profile",
    "You have unread notifications",
    "Your network is growing",
    "New job recommendations for you",
    "{name} mentioned you in a post",
    "Your profile views this week",
    "People are finding your profile",
    "You have a pending connection request",
    "{name} endorsed your skills",
    "New opportunities matching your profile",
    "Your connection request was accepted",
    "People you may know on LinkedIn",
    "{name} commented on your post",
    "Your post is getting noticed",
    "Weekly summary: your LinkedIn activity",
    "You appeared in search results this week"

]

linkedin_bodies = [
    "Hi {name}, you have a new connection request waiting. View it here: {link}",
    "Hello {name}, your profile was viewed 5 times this week. See who is interested: {link}",
    "Hi {name}, you have a new message waiting in your inbox. Read it here: {link}",
    "Hello {name}, several people have viewed your profile recently. Check who: {link}",
    "Hi {name}, you have unread notifications waiting. Catch up here: {link}",
    "Hello {name}, your network has grown this week. See your new connections: {link}",
    "Hi {name}, we found some job recommendations that match your profile. View them here: {link}",
    "Hello {name}, you were mentioned in a recent post. See it here: {link}",
    "Hi {name}, here is your weekly summary of profile activity: {link}",
    "Hello {name}, someone from your industry just viewed your profile. Check it out: {link}",
    "Hi {name}, your skills were endorsed by a connection this week. View your profile: {link}",
    "Hello {name}, your connection request has been accepted. View their profile here: {link}",
    "Hi {name}, you appeared in search results this week. See who found you: {link}",
    "Hello {name}, we have found people you may know on LinkedIn. Connect here: {link}",
    "Hi {name}, your recent post is gaining traction. See the engagement here: {link}",
    "Hello {name}, new job opportunities matching your experience have been posted. View: {link}",
    "Hi {name}, a connection commented on your post recently. Read the thread here: {link}",
    "Hello {name}, your profile activity summary for this week is ready. View it: {link}",
    "Hi {name}, you have a pending connection request from someone in your field. View: {link}",
    "Hello {name}, your LinkedIn digest for this week is ready. Catch up here: {link}"
    "Hi {name}, please confirm your email address to continue receiving LinkedIn notifications: {link}",
    "Hello {name}, action required: please review and update your LinkedIn profile details: {link}",
    "Hi {name}, please verify your account to continue accessing LinkedIn premium features: {link}",
    "Hello {name}, we need you to confirm your identity to keep your LinkedIn account secure: {link}",
    "Hi {name}, please review your account settings and confirm your preferences here: {link}"
]

coursera_subjects = [
    "Continue your course: {course}",
    "New assignment posted in {course}",
    "Your certificate is ready",
    "Reminder: complete your weekly lesson",
    "Your progress in {course}",
    "New course recommendation for you",
    "Do not lose your learning streak",
    "Upcoming deadline for {course}",
    "New content available in {course}",
    "Your weekly learning summary",
    "You are close to finishing {course}",
    "Your quiz results for {course}",
    "New discussion post in {course}",
    "Your instructor left feedback in {course}",
    "Module unlocked in {course}",
    "Resume where you left off in {course}",
    "Your peer review is ready in {course}",
    "Congratulations on completing a module",
    "Your course progress report: {course}",
    "New video lesson available in {course}"
]

coursera_bodies = [
    "Hi {name}, you are making great progress in {course}. Continue learning here: {link}",
    "Hello {name}, a new assignment has been posted in {course}. View it here: {link}",
    "Hi {name}, your certificate for {course} is ready to download: {link}",
    "Hello {name}, do not forget to complete this week's lesson in {course}. Continue here: {link}",
    "Hi {name}, here is a quick look at your progress in {course} so far. View details: {link}",
    "Hello {name}, based on your interests, we recommend a new course. Explore it here: {link}",
    "Hi {name}, you are on a learning streak. Keep it going with {course}: {link}",
    "Hello {name}, your assignment for {course} is due soon. Submit it here: {link}",
    "Hi {name}, new content has just been added to {course}. Check it out: {link}",
    "Hello {name}, here is your weekly learning summary across all your courses: {link}",
    "Hi {name}, you are close to finishing {course}. Just a few lessons left: {link}",
    "Hello {name}, your quiz results for {course} are now available. View them here: {link}",
    "Hi {name}, there is a new discussion thread in {course} you may want to join: {link}",
    "Hello {name}, your instructor left feedback on your recent submission in {course}: {link}",
    "Hi {name}, a new module has been unlocked in {course}. Start it here: {link}",
    "Hello {name}, pick up where you left off in {course}. Resume here: {link}",
    "Hi {name}, your peer review submission is ready to view in {course}: {link}",
    "Hello {name}, congratulations on completing a module in {course}. Keep going: {link}",
    "Hi {name}, here is your course progress report for {course} this week: {link}",
    "Hello {name}, a new video lesson is available in {course}. Watch it here: {link}"
    "Hi {name}, please confirm your enrolment in {course} to secure your place: {link}",
    "Hello {name}, action required: please review and submit your assignment for {course} before the deadline: {link}",
    "Hi {name}, please verify your account details to continue accessing {course}: {link}",
    "Hello {name}, please confirm your course preferences for {course} to continue your learning: {link}",
    "Hi {name}, we need you to review and confirm your progress in {course}: {link}"    
]

paypal_subjects = [
    "You sent a payment of {amount}",
    "Payment confirmation: {amount}",
    "Your PayPal receipt",
    "You have received a payment",
    "Your transaction summary",
    "Payment to {name} successful",
    "Your account activity update",
    "A payment was made from your account",
    "Your monthly PayPal summary",
    "Receipt for your recent transaction",
    "Your payment of {amount} is complete",
    "Money sent: {amount}",
    "Transaction confirmed: {amount}",
    "You have a new PayPal notification",
    "Your PayPal balance has been updated",
    "Payment received: {amount}",
    "Your recent PayPal activity",
    "Transfer of {amount} completed",
    "Your PayPal account statement",
    "Confirmation of your recent payment"
]

paypal_bodies = [
    "Hi {name}, your payment of {amount} has been sent successfully. View receipt: {link}",
    "Hello {name}, we have confirmed your recent payment of {amount}. Details here: {link}",
    "Hi {name}, you have received a payment. Log in to view details: {link}",
    "Hello {name}, here is your receipt for the recent transaction of {amount}. View it here: {link}",
    "Hi {name}, your transaction summary for this month is ready. Review it here: {link}",
    "Hello {name}, your account activity has been updated following a recent payment. Details: {link}",
    "Hi {name}, a payment of {amount} was processed from your account. View details: {link}",
    "Hello {name}, your monthly PayPal summary is now available. View it here: {link}",
    "Hi {name}, thank you for your payment of {amount}. Your receipt is ready: {link}",
    "Hello {name}, your recent transaction has been completed successfully. View receipt: {link}",
    "Hi {name}, a transfer of {amount} has been completed from your account. Details: {link}",
    "Hello {name}, your PayPal balance has been updated following a recent transaction: {link}",
    "Hi {name}, money has been sent successfully. View your transaction history here: {link}",
    "Hello {name}, you have a new notification regarding your PayPal account. View it: {link}",
    "Hi {name}, payment of {amount} confirmed. Your updated account statement is here: {link}",
    "Hello {name}, you have received {amount} in your PayPal account. View details: {link}",
    "Hi {name}, here is a summary of your recent PayPal activity: {link}",
    "Hello {name}, your recent payment of {amount} to a merchant has been processed: {link}",
    "Hi {name}, your PayPal account statement is now ready to view and download: {link}",
    "Hello {name}, we have processed your payment and your receipt is now available: {link}"
    "Hi {name}, please confirm your payment details to complete your recent transaction of {amount}: {link}",
    "Hello {name}, action required: please review and confirm your recent PayPal activity: {link}",
    "Hi {name}, please verify your billing address to continue processing payments: {link}",
    "Hello {name}, please update your payment method to avoid any disruption to your service: {link}",
    "Hi {name}, we need you to confirm your recent transaction of {amount} was authorised: {link}"
]

banking_subjects = [
    "Your monthly statement is ready",
    "Account balance update",
    "Transaction alert: {amount}",
    "Your statement for {date} is available",
    "Your account activity summary",
    "A new transaction was recorded",
    "Your direct debit has been processed",
    "Your savings account update",
    "Important account notification",
    "Your weekly balance summary",
    "Your account has been credited",
    "Standing order processed: {amount}",
    "Your new statement is available online",
    "Recent transaction on your account",
    "Your overdraft limit notification",
    "Card payment confirmed: {amount}",
    "Your ISA statement is ready",
    "Scheduled payment processed",
    "Your account summary for {date}",
    "New transaction posted to your account"
]

banking_bodies = [
    "Hi {name}, your monthly account statement is now available. View it here: {link}",
    "Hello {name}, a transaction of {amount} was recorded on your account. Details: {link}",
    "Hi {name}, your account balance was updated on {date}. Log in to view: {link}",
    "Hello {name}, your account activity summary for this period is ready. View it here: {link}",
    "Hi {name}, a direct debit of {amount} was processed from your account on {date}. Details: {link}",
    "Hello {name}, your savings account balance was updated. View your new balance here: {link}",
    "Hi {name}, here is an important notification regarding your account. View details: {link}",
    "Hello {name}, your weekly balance summary is ready to view. Log in here: {link}",
    "Hi {name}, a new transaction of {amount} has been recorded on your statement. View it here: {link}",
    "Hello {name}, your account statement for {date} is now ready to download: {link}",
    "Hi {name}, your account has been credited with {amount}. View your updated balance: {link}",
    "Hello {name}, a standing order of {amount} has been processed from your account: {link}",
    "Hi {name}, a card payment of {amount} has been confirmed on your account. Details: {link}",
    "Hello {name}, your ISA statement is now available to view online. Access it here: {link}",
    "Hi {name}, a scheduled payment of {amount} has been processed from your account: {link}",
    "Hello {name}, a new transaction has been posted to your account. Review it here: {link}",
    "Hi {name}, your account summary for {date} is now available. View it here: {link}",
    "Hello {name}, we wanted to let you know about a recent transaction on your account: {link}",
    "Hi {name}, your monthly statement is ready and available in your online banking portal: {link}",
    "Hello {name}, your direct debit schedule has been updated. View the changes here: {link}"
    "Hi {name}, please confirm your account details to complete your recent transaction of {amount}: {link}",
    "Hello {name}, action required: please review and confirm your recent account activity: {link}",
    "Hi {name}, please verify your contact details to ensure you continue receiving account notifications: {link}",
    "Hello {name}, please update your direct debit details to avoid any disruption to your payments: {link}",
    "Hi {name}, we need you to confirm your identity to complete a recent account update: {link}"   
]

it_subjects = [
    "Scheduled maintenance on {date}",
    "Password expiry reminder",
    "New software update available",
    "Action required: update your device",
    "Your IT support ticket update",
    "VPN access renewal required",
    "New security policy update",
    "Your device compliance check",
    "Software licence renewal reminder",
    "System downtime notice for {date}",
    "Your remote access certificate expires soon",
    "New company-wide software rollout",
    "IT helpdesk: your ticket has been resolved",
    "Mandatory system update required",
    "Your multi-factor authentication setup",
    "Network maintenance planned for {date}",
    "Your email storage limit notification",
    "IT security awareness reminder",
    "Your workplace account has been updated",
    "Reminder: complete your IT compliance training"
]

it_bodies = [
    "Hi {name}, scheduled system maintenance will occur on {date}. More details: {link}",
    "Hello {name}, your password will expire soon. Update it here: {link}",
    "Hi {name}, a new software update is available for your device. Install it here: {link}",
    "Hello {name}, your IT support ticket has been updated. View the latest status here: {link}",
    "Hi {name}, your VPN access is due for renewal. Renew it here to avoid interruption: {link}",
    "Hello {name}, a new security policy has been introduced. Review the changes here: {link}",
    "Hi {name}, your device is due for a routine compliance check. Schedule it here: {link}",
    "Hello {name}, your software licence is due for renewal soon. Renew it here: {link}",
    "Hi {name}, please note there will be system downtime on {date} for scheduled updates: {link}",
    "Hello {name}, your account requires a routine IT review. Complete it here: {link}",
    "Hi {name}, your remote access certificate is expiring soon. Renew it here: {link}",
    "Hello {name}, a new software rollout is being deployed company-wide. Details here: {link}",
    "Hi {name}, your IT helpdesk ticket has been resolved. View the resolution here: {link}",
    "Hello {name}, a mandatory system update has been scheduled for your device. Install: {link}",
    "Hi {name}, please complete your multi-factor authentication setup by {date}: {link}",
    "Hello {name}, network maintenance is planned for {date}. See which services are affected: {link}",
    "Hi {name}, your email storage is approaching its limit. Manage your storage here: {link}",
    "Hello {name}, this is a reminder to complete your annual IT security awareness training: {link}",
    "Hi {name}, your workplace account settings have been updated. Review the changes here: {link}",
    "Hello {name}, please complete your IT compliance training by {date}. Access it here: {link}"
    "Hi {name}, please confirm your device compliance status to continue accessing company systems: {link}",
    "Hello {name}, action required: please review and confirm the recent changes to your account: {link}",
    "Hi {name}, please verify your identity to complete the IT security check on your account: {link}",
    "Hello {name}, please update your VPN credentials to continue accessing company resources: {link}",
    "Hi {name}, we need you to confirm your software licence details before renewal: {link}"
]

#phishing emails
credential_subjects = [
    "Action required: verify your Amazon account",
    "Your PayPal account needs confirmation",
    "LinkedIn: please verify your login details",
    "Unusual sign-in detected on your account",
    "Your Coursera account requires verification",
    "Please confirm your banking credentials",
    "Your account access will be restricted",
    "We need to verify your identity",
    "Login verification needed for your account",
    "Important: confirm your account details",
    "Your account security check is required",
    "Verify your details to continue",
    "Action needed: confirm your login",
    "Your account requires immediate attention",
    "Please re-authenticate your account",
    "Security check: confirm your details",
    "Your session requires confirmation",
    "We detected an issue with your account",
    "Account verification request",
    "Re-verify your login to continue"
]

credential_bodies = [
    "Hi {name}, we noticed unusual activity on your Amazon account. Your order {order_id} could not be verified. Please confirm your account details to continue: {link}",
    "Hello {name}, your PayPal account requires verification following a recent payment of {amount}. Please confirm your details here to avoid any disruption: {link}",
    "Hi {name}, we noticed a sign-in to your LinkedIn account from an unrecognised device. Please verify your credentials to secure your account: {link}",
    "Hello {name}, your Coursera account requires re-authentication to continue accessing {course}. Please confirm your login details here: {link}",
    "Hi {name}, your banking account requires verification following recent account activity. Please confirm your details to maintain access: {link}",
    "Hello {name}, we were unable to verify your recent Amazon order {order_id}. Please confirm your account details to complete your purchase: {link}",
    "Hi {name}, your PayPal account has been flagged for a routine security check. Please verify your identity here to continue: {link}",
    "Hello {name}, your LinkedIn account credentials need to be updated. Please confirm your login details to avoid restricted access: {link}",
    "Hi {name}, your account requires verification before your next billing cycle of {amount}. Please confirm your details here: {link}",
    "Hello {name}, we need to confirm it was you who recently signed in. Please verify your account details here to continue: {link}",
    "Hi {name}, as part of our security process, we need you to confirm your login credentials. Please verify here: {link}",
    "Hello {name}, your account details need to be reconfirmed for continued access. Please complete this short verification: {link}",
    "Hi {name}, immediate verification is required to maintain uninterrupted access to your account. Please confirm here: {link}",
    "Hello {name}, we require you to re-verify your credentials at this time. Please complete the process here: {link}",
    "Hi {name}, a security check has been triggered on your account. Please confirm your details to continue: {link}",
    "Hello {name}, please confirm your account details to ensure continued secure access to your services: {link}",
    "Hi {name}, your current session requires confirmation to proceed. Please verify your details here: {link}",
    "Hello {name}, we are reaching out to confirm your account is secure. Please complete the verification here: {link}",
    "Hi {name}, your account verification is overdue. Please complete it here to continue using your services: {link}",
    "Hello {name}, please confirm your account details to avoid any disruption to your service: {link}"
]

suspension_subjects = [
    "Your Amazon account has been temporarily suspended",
    "Your PayPal account is under review",
    "LinkedIn: your account may be restricted soon",
    "Action needed to keep your account active",
    "Your account status has changed",
    "Immediate action required on your account",
    "Your account may be limited soon",
    "We need to verify your account status",
    "Your account is pending review",
    "Final reminder: confirm your account details",
    "Your account has been flagged for review",
    "Account restriction notice",
    "Urgent: your account requires attention",
    "Your access may be limited",
    "Account review in progress",
    "We have placed a hold on your account",
    "Action required to restore full access",
    "Your account privileges are under review",
    "Notice: account activity flagged",
    "Your account status update"
]

suspension_bodies = [
    "Hi {name}, your Amazon account has been temporarily suspended due to unusual activity on order {order_id}. Please confirm your details within 48 hours to restore access: {link}",
    "Hello {name}, your PayPal account is currently under review following a transaction of {amount}. Please confirm your information here to avoid restrictions: {link}",
    "Hi {name}, your LinkedIn account has been flagged for review. Please confirm your details to avoid suspension of your account: {link}",
    "Hello {name}, your account may be limited soon unless you verify your details. Please complete this confirmation to keep your account active: {link}",
    "Hi {name}, your account status has recently changed following a review of recent activity. Please confirm your details here: {link}",
    "Hello {name}, immediate action is needed to prevent limited access to your account. Please confirm your details here: {link}",
    "Hi {name}, we need to verify your current account status. Please confirm your details here to continue: {link}",
    "Hello {name}, your account is currently pending review. Please confirm your information to continue using our services: {link}",
    "Hi {name}, this is a final reminder to confirm your account details before access is limited: {link}",
    "Hello {name}, please complete this brief confirmation to keep your account in good standing: {link}",
    "Hi {name}, we have placed a temporary hold on your account pending verification. Please confirm your details here: {link}",
    "Hello {name}, your account privileges are currently under review. Please provide confirmation to continue: {link}",
    "Hi {name}, we have flagged recent activity on your account and require your confirmation to proceed: {link}",
    "Hello {name}, to restore full access to your account, please complete this verification process: {link}",
    "Hi {name}, your account requires attention to avoid an upcoming restriction. Please act here: {link}",
    "Hello {name}, we are conducting a routine account review and need your confirmation to proceed: {link}",
    "Hi {name}, your account has been placed under review following recent activity. Please confirm here: {link}",
    "Hello {name}, please verify your account details to prevent any disruption to your service: {link}",
    "Hi {name}, an account status update requires your attention. Please review and confirm here: {link}",
    "Hello {name}, action is required to maintain your current level of account access: {link}"
]

payment_subjects = [
    "Your Amazon payment of {amount} could not be processed",
    "PayPal: update your billing information",
    "Your subscription payment of {amount} failed",
    "We could not process your recent payment",
    "Action needed: billing issue on your account",
    "Your payment method needs attention",
    "Please review your payment details",
    "Your account billing requires confirmation",
    "We need to verify your payment method",
    "Your recent charge of {amount} could not be completed",
    "Billing update required on your account",
    "Your payment is on hold",
    "Resolve a payment issue on your account",
    "Outstanding balance of {amount} on your account",
    "Payment declined: action required",
    "Your billing cycle update",
    "Confirm your payment method to continue",
    "We were unable to charge your account",
    "Your subscription renewal needs attention",
    "Your invoice of {amount} is ready for review"
]

payment_bodies = [
    "Hi {name}, we were unable to process your recent Amazon payment of {amount} for order {order_id}. Please update your billing details here to complete your purchase: {link}",
    "Hello {name}, your PayPal payment method requires verification before your next billing cycle. Please confirm your details here to avoid any disruption: {link}",
    "Hi {name}, your subscription payment of {amount} did not go through. Please update your billing details here to continue your service: {link}",
    "Hello {name}, we detected a billing issue on your account related to a recent charge of {amount}. Please review and update your details here: {link}",
    "Hi {name}, there was an issue processing your payment of {amount}. Please update your information here to avoid service interruption: {link}",
    "Hello {name}, please review your payment details to avoid any disruption to your service: {link}",
    "Hi {name}, your account billing needs to be confirmed to continue without interruption. Please update here: {link}",
    "Hello {name}, we need to verify your current payment method on file. Please confirm it here: {link}",
    "Hi {name}, your recent charge of {amount} could not be completed. Please update your details here: {link}",
    "Hello {name}, to avoid any disruption to your account, please confirm your billing information here: {link}",
    "Hi {name}, your payment of {amount} is currently on hold pending verification. Please resolve it here: {link}",
    "Hello {name}, there is an outstanding balance of {amount} on your account. Please settle it here: {link}",
    "Hi {name}, your payment was declined. Please update your billing details to continue your service: {link}",
    "Hello {name}, we were unable to charge your account for the recent billing cycle. Please update here: {link}",
    "Hi {name}, your subscription renewal of {amount} requires your attention. Please confirm here: {link}",
    "Hello {name}, a billing update is required on your account to avoid service interruption: {link}",
    "Hi {name}, your invoice for {amount} is ready. Please review and confirm payment here: {link}",
    "Hello {name}, please confirm your payment method to ensure uninterrupted service: {link}",
    "Hi {name}, we could not process the {amount} charge on your account. Please review here: {link}",
    "Hello {name}, action is required to resolve a payment issue on your account: {link}"
]

delivery_subjects = [
    "Your Amazon delivery could not be completed",
    "Action required: confirm your delivery address",
    "Your package from order {order_id} is on hold",
    "We could not deliver your parcel today",
    "Your shipment requires address confirmation",
    "Delivery attempt failed for order {order_id}",
    "Your package is awaiting confirmation",
    "Delivery rescheduling required",
    "Outstanding customs fee on your shipment",
    "Your parcel could not be delivered as scheduled",
    "Delivery exception on your recent order",
    "Your package is being held at the depot",
    "Missed delivery: reschedule now",
    "Customs clearance required for your parcel",
    "Your delivery window has been updated",
    "We need your address confirmation to proceed",
    "Your parcel is ready for collection",
    "Delivery failed: address unconfirmed",
    "Action required to release your shipment",
    "Your package delivery update for order {order_id}"
]

delivery_bodies = [
    "Hi {name}, we attempted to deliver your Amazon order {order_id} but were unable to confirm your address. Please update your delivery details here: {link}",
    "Hello {name}, your package from order {order_id} is currently on hold pending address confirmation. Please confirm your details here to release your delivery: {link}",
    "Hi {name}, your parcel is being held at the local depot pending a small customs fee of {amount}. Please complete payment here to release your delivery: {link}",
    "Hello {name}, delivery of your order {order_id} could not be completed. Please confirm your address here to reschedule: {link}",
    "Hi {name}, your shipment is currently on hold pending address verification. Please confirm your details here: {link}",
    "Hello {name}, your package is awaiting confirmation before it can be delivered. Please confirm here: {link}",
    "Hi {name}, we need to reschedule your delivery for order {order_id}. Please confirm a suitable time here: {link}",
    "Hello {name}, there is an outstanding customs fee on your shipment that needs to be settled: {link}",
    "Hi {name}, your parcel could not be delivered as scheduled. Please review your details here to rearrange: {link}",
    "Hello {name}, please complete this short confirmation to release your pending delivery: {link}",
    "Hi {name}, a delivery exception has occurred on your order {order_id}. Please review the details here: {link}",
    "Hello {name}, your parcel is currently being held at the local depot. Please arrange collection here: {link}",
    "Hi {name}, you missed a delivery attempt for order {order_id}. Please reschedule your delivery here: {link}",
    "Hello {name}, customs clearance is required for your parcel before it can be delivered. Complete the process here: {link}",
    "Hi {name}, your delivery window has been updated for order {order_id}. Please confirm the new time slot here: {link}",
    "Hello {name}, we need your address confirmation before we can release your shipment: {link}",
    "Hi {name}, your parcel is ready for collection at a nearby pickup point. Please view details here: {link}",
    "Hello {name}, your delivery could not be completed as your address could not be confirmed: {link}",
    "Hi {name}, action is required to release your shipment from the delivery hold. Please complete here: {link}",
    "Hello {name}, here is an update on your delivery for order {order_id}. Please confirm your details here: {link}"
]

security_subjects = [
    "Security alert: new sign-in to your Amazon account",
    "Your PayPal account was accessed from a new device",
    "LinkedIn: we detected a login from an unrecognised location",
    "Your password may have been compromised",
    "Important: review recent activity on your account",
    "Unusual activity detected on your account",
    "Your account security needs attention",
    "We noticed a new login location on your account",
    "Please review this recent sign-in",
    "Your account safety check is required",
    "Security notice: action recommended",
    "New sign-in detected on your account",
    "Your account was accessed from a new location",
    "We have flagged suspicious activity on your account",
    "Password reset recommended for your account",
    "Potential unauthorised access detected",
    "Your security settings have changed",
    "Review your recent account access",
    "We recommend securing your account now",
    "Your account protection update"
]

security_bodies = [
    "Hi {name}, we detected a new sign-in to your Amazon account from an unrecognised device. If this was not you, please secure your account immediately: {link}",
    "Hello {name}, your PayPal account was accessed from a new location following a recent transaction of {amount}. Please confirm this was you here: {link}",
    "Hi {name}, we noticed a sign-in to your LinkedIn account from an unrecognised location. Please review this activity and secure your account if needed: {link}",
    "Hello {name}, your account password may have been compromised in a recent data exposure. Please reset it now to stay protected: {link}",
    "Hi {name}, please review recent activity on your account and confirm it was you who signed in: {link}",
    "Hello {name}, we have noticed unusual activity on your account recently. Please review it here and take action if needed: {link}",
    "Hi {name}, your account security may need attention following a recent alert. Please review here: {link}",
    "Hello {name}, we noticed a login from a location you have not used before. Please confirm this was you here: {link}",
    "Hi {name}, please take a moment to review this recent sign-in to your account and confirm it was authorised: {link}",
    "Hello {name}, we recommend completing a quick account safety check at this time: {link}",
    "Hi {name}, for your protection, please confirm the recent activity on your account here: {link}",
    "Hello {name}, we have issued a security notice for your account. Please take action here: {link}",
    "Hi {name}, a new sign-in to your account was detected from an unfamiliar device. Please review here: {link}",
    "Hello {name}, your account was accessed from a new location. Please confirm this was you here: {link}",
    "Hi {name}, we have flagged suspicious activity on your account. Please review and secure it here: {link}",
    "Hello {name}, we recommend resetting your password as a precaution following a recent security alert: {link}",
    "Hi {name}, please review your recent account access to confirm all activity was authorised: {link}",
    "Hello {name}, we recommend taking steps to secure your account following a recent alert: {link}",
    "Hi {name}, an unrecognised login attempt was made on your account. Please review it here: {link}",
    "Hello {name}, here is an update on your account protection status. Please review and take action if needed: {link}"
]

def generate_email(email_id, label, category, subjects, bodies):
    name = random.choice(names)
    order_id = f"#{random.randint(100000, 999999)}"
    amount = f"${random.randint(15, 250)}.{random.randint(0,99):02d}"
    date = random.choice(["Tuesday", "Thursday", "this Friday", "next Monday"])
    course = random.choice(courses)

    subject = random.choice(subjects).format( name=name, order_id=order_id, course=course, amount=amount, date=date, link="" )
    body = random.choice(bodies).format(
    name=name, order_id=order_id, amount=amount, date=date, link="", course=course
)

    return {
        "id": email_id,
        "label": label,
        "category": category,
        "subject": subject,
        "body": body
    }
    
#legitimate loops
all_emails = []
email_id = 0

for i in range(417):
    all_emails.append(generate_email(
    email_id, "legitimate", "amazon_order", amazon_subjects, amazon_bodies
    ))
    email_id += 1

for i in range(417):
    all_emails.append(generate_email(
        email_id, "legitimate", "linkedin_notification", linkedin_subjects, linkedin_bodies
    ))
    email_id += 1
for i in range(417):
    all_emails.append(generate_email(
        email_id, "legitimate", "coursera_notification", coursera_subjects, coursera_bodies
    ))
    email_id += 1

for i in range(417):
    all_emails.append(generate_email(
        email_id, "legitimate", "paypal_payment", paypal_subjects, paypal_bodies
    ))
    email_id += 1

for i in range(417):
    all_emails.append(generate_email(
        email_id, "legitimate", "banking_notification", banking_subjects, banking_bodies
    ))
    email_id += 1

for i in range(417):
    all_emails.append(generate_email(
        email_id, "legitimate", "corporate_it", it_subjects, it_bodies
    ))
    email_id += 1
    
#phishing loops
for i in range(500):
    all_emails.append(generate_email(
        email_id, "phishing", "credential_harvesting",
        credential_subjects, credential_bodies
    ))
    email_id += 1

for i in range(500):
    all_emails.append(generate_email(
        email_id, "phishing", "account_suspension",
        suspension_subjects, suspension_bodies
    ))
    email_id += 1

for i in range(500):
    all_emails.append(generate_email(
        email_id, "phishing", "payment_verification",
        payment_subjects, payment_bodies
    ))
    email_id += 1

for i in range(500):
    all_emails.append(generate_email(
        email_id, "phishing", "delivery_notification",
        delivery_subjects, delivery_bodies
    ))
    email_id += 1

for i in range(500):
    all_emails.append(generate_email(
        email_id, "phishing", "security_alert",
        security_subjects, security_bodies
    ))
    email_id += 1

with open("emails.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "label", "category", "subject", "body"])
    writer.writeheader()
    writer.writerows(all_emails)

print(f"Generated {len(all_emails)} emails and saved to emails.csv")