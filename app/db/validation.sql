-- =============================================================================
-- Database Integrity & Validation Suite (PostgreSQL)
-- Environment: dev | Region: us-central1
--
-- READ-ONLY validation queries to verify:
-- 1. Table row counts across all 10 schema entities
-- 2. Foreign key integrity / orphaned row detection
-- 3. Monetary value & financial math correctness
-- 4. Tenant isolation & leakage risk checks
-- 5. Business status & priority distribution analytics
-- =============================================================================

-- -----------------------------------------------------------------------------
-- CHECK 1: ROW COUNTS ACROSS ALL ENTITIES
-- -----------------------------------------------------------------------------
SELECT 'tenants' AS entity_name, COUNT(*) AS row_count FROM tenants
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'support_tickets', COUNT(*) FROM support_tickets
UNION ALL
SELECT 'ticket_events', COUNT(*) FROM ticket_events
UNION ALL
SELECT 'approval_requests', COUNT(*) FROM approval_requests
UNION ALL
SELECT 'agent_action_audit', COUNT(*) FROM agent_action_audit
ORDER BY entity_name;

-- -----------------------------------------------------------------------------
-- CHECK 2: ORPHANED ROWS DETECTION (EXPECTED RESULT: 0 ROWS FOR ALL CHECKS)
-- -----------------------------------------------------------------------------
-- 2a. Orders without valid customers
SELECT 'orphaned_orders_no_customer' AS check_type, COUNT(*) AS invalid_count
FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 2b. Order Items without valid orders or products
SELECT 'orphaned_order_items_no_order' AS check_type, COUNT(*) AS invalid_count
FROM order_items oi LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'orphaned_order_items_no_product', COUNT(*)
FROM order_items oi LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

-- 2c. Payments without valid orders
SELECT 'orphaned_payments_no_order' AS check_type, COUNT(*) AS invalid_count
FROM payments p LEFT JOIN orders o ON p.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 2d. Support tickets without valid customers
SELECT 'orphaned_tickets_no_customer' AS check_type, COUNT(*) AS invalid_count
FROM support_tickets st LEFT JOIN customers c ON st.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 2e. Ticket events without valid support tickets
SELECT 'orphaned_events_no_ticket' AS check_type, COUNT(*) AS invalid_count
FROM ticket_events te LEFT JOIN support_tickets st ON te.support_ticket_id = st.support_ticket_id
WHERE st.support_ticket_id IS NULL;

-- -----------------------------------------------------------------------------
-- CHECK 3: MONETARY VALUE & SUB-TOTAL MATHEMATICAL INTEGRITY
-- Expected: 0 invalid rows for negative prices, amounts, or subtotal mismatches
-- -----------------------------------------------------------------------------
-- 3a. Negative monetary values
SELECT 'negative_product_price' AS issue_type, COUNT(*) AS violation_count FROM products WHERE unit_price < 0
UNION ALL
SELECT 'negative_order_total', COUNT(*) FROM orders WHERE total_amount < 0
UNION ALL
SELECT 'negative_order_item_price', COUNT(*) FROM order_items WHERE unit_price < 0 OR subtotal < 0
UNION ALL
SELECT 'negative_payment_amount', COUNT(*) FROM payments WHERE amount < 0;

-- 3b. Order line item subtotal calculation mismatch (subtotal != quantity * unit_price)
SELECT oi.order_item_id, oi.order_id, oi.quantity, oi.unit_price, oi.subtotal,
       (oi.quantity * oi.unit_price) AS calculated_subtotal
FROM order_items oi
WHERE oi.subtotal <> (oi.quantity * oi.unit_price);

-- 3c. Order total amount mismatch vs sum of order_items subtotals
SELECT o.order_id, o.order_number, o.total_amount, SUM(oi.subtotal) AS sum_items_subtotal
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.order_number, o.total_amount
HAVING o.total_amount <> SUM(oi.subtotal);

-- -----------------------------------------------------------------------------
-- CHECK 4: TENANT LEAKAGE RISK VALIDATION
-- Validates cross-tenant reference safety. (EXPECTED RESULT: 0 ROWS FOR ALL CHECKS)
-- -----------------------------------------------------------------------------
-- 4a. Orders associated with a customer from a different tenant
SELECT 'tenant_leakage_orders_customer' AS risk_type, COUNT(*) AS violation_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.tenant_id <> c.tenant_id;

-- 4b. Order items associated with an order from a different tenant
SELECT 'tenant_leakage_order_items_order' AS risk_type, COUNT(*) AS violation_count
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE oi.tenant_id <> o.tenant_id;

-- 4c. Order items associated with a product from a different tenant
SELECT 'tenant_leakage_order_items_product' AS risk_type, COUNT(*) AS violation_count
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
WHERE oi.tenant_id <> p.tenant_id;

-- 4d. Payments associated with an order from a different tenant
SELECT 'tenant_leakage_payments_order' AS risk_type, COUNT(*) AS violation_count
FROM payments p
JOIN orders o ON p.order_id = o.order_id
WHERE p.tenant_id <> o.tenant_id;

-- 4e. Support tickets associated with a customer from a different tenant
SELECT 'tenant_leakage_tickets_customer' AS risk_type, COUNT(*) AS violation_count
FROM support_tickets st
JOIN customers c ON st.customer_id = c.customer_id
WHERE st.tenant_id <> c.tenant_id;

-- 4f. Support tickets associated with an order from a different tenant
SELECT 'tenant_leakage_tickets_order' AS risk_type, COUNT(*) AS violation_count
FROM support_tickets st
JOIN orders o ON st.order_id = o.order_id
WHERE st.tenant_id <> o.tenant_id;

-- 4g. Ticket events associated with a support ticket from a different tenant
SELECT 'tenant_leakage_events_ticket' AS risk_type, COUNT(*) AS violation_count
FROM ticket_events te
JOIN support_tickets st ON te.support_ticket_id = st.support_ticket_id
WHERE te.tenant_id <> st.tenant_id;

-- 4h. Approval requests associated with a support ticket from a different tenant
SELECT 'tenant_leakage_approvals_ticket' AS risk_type, COUNT(*) AS violation_count
FROM approval_requests ar
JOIN support_tickets st ON ar.support_ticket_id = st.support_ticket_id
WHERE ar.tenant_id <> st.tenant_id;

-- -----------------------------------------------------------------------------
-- CHECK 5: BUSINESS-STATUS & PRIORITY DISTRIBUTIONS
-- Verifies synthetic coverage across normal, urgent, closed, pending, late, refunded, rejected
-- -----------------------------------------------------------------------------
-- 5a. Order status breakdown
SELECT order_status, COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;

-- 5b. Payment status breakdown
SELECT payment_status, COUNT(*) AS payment_count
FROM payments
GROUP BY payment_status
ORDER BY payment_count DESC;

-- 5c. Support ticket status & priority breakdown
SELECT status AS ticket_status, priority AS ticket_priority, COUNT(*) AS ticket_count
FROM support_tickets
GROUP BY status, priority
ORDER BY status, priority;

-- 5d. HITL Approval request status breakdown
SELECT status AS approval_status, request_type, COUNT(*) AS request_count
FROM approval_requests
GROUP BY status, request_type
ORDER BY status;

-- 5e. Agent Action Audit execution status breakdown
SELECT execution_status, agent_role, COUNT(*) AS action_count
FROM agent_action_audit
GROUP BY execution_status, agent_role
ORDER BY execution_status;
