-- =============================================================================
-- Deterministic Synthetic Seed Data for Customer Operations Lab (PostgreSQL)
-- Environment: dev | Region: us-central1
--
-- Rules & Guidelines:
-- - Synthetic data ONLY. Uses reserved example domains (example.com, example.org).
-- - Fictional names, company entities, addresses, and transaction references.
-- - Strictly NO sensitive secrets, credentials, or real payment card details.
-- - Includes normal, urgent, closed, pending, late, refunded, and rejected cases.
-- - Fully idempotent using ON CONFLICT DO NOTHING clauses.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. TENANTS
-- -----------------------------------------------------------------------------
INSERT INTO tenants (tenant_id, name, slug, status)
VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Acme Logistics Corp', 'acme-logistics', 'active'),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Globex Retail Solutions', 'globex-retail', 'active')
ON CONFLICT (tenant_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. CUSTOMERS
-- -----------------------------------------------------------------------------
INSERT INTO customers (customer_id, tenant_id, external_customer_ref, first_name, last_name, email, phone_number, company_name, status)
VALUES
    ('c0000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CUST-ACME-001', 'Alice', 'Smith', 'alice.smith@example.com', '+1-555-0101', 'Nexus Systems Ltd', 'active'),
    ('c0000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CUST-ACME-002', 'Bob', 'Jones', 'bob.jones@example.com', '+1-555-0102', 'Apex Retail Group', 'active'),
    ('c0000000-0000-4000-a000-000000000003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CUST-ACME-003', 'Charlie', 'Brown', 'charlie.brown@example.org', '+1-555-0103', 'Starlight Logistics', 'flagged'),
    ('c0000000-0000-4000-b000-000000000004', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'CUST-GLOBEX-001', 'Diana', 'Prince', 'diana.prince@example.net', '+1-555-0201', 'Wayne Enterprises', 'active'),
    ('c0000000-0000-4000-b000-000000000005', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'CUST-GLOBEX-002', 'Evan', 'Wright', 'evan.wright@example.com', '+1-555-0202', 'Cyberdyne Systems', 'active')
ON CONFLICT (customer_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. PRODUCTS
-- -----------------------------------------------------------------------------
INSERT INTO products (product_id, tenant_id, sku, name, description, unit_price, currency, stock_quantity, status)
VALUES
    ('p0000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SKU-ACME-1001', 'Industrial IoT Sensor Module v1', 'High precision vibration and temp sensor', 150.00, 'USD', 50, 'active'),
    ('p0000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SKU-ACME-1002', 'Enterprise Network Router Rack Unit', '10GbE enterprise core router', 1200.00, 'USD', 12, 'active'),
    ('p0000000-0000-4000-a000-000000000003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SKU-ACME-1003', 'High-Speed Fiber Optic Patch Cable 50m', 'Armored multimode fiber cable', 45.00, 'USD', 200, 'active'),
    ('p0000000-0000-4000-b000-000000000001', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'SKU-GLOB-2001', 'Smart POS Terminal Countertop', 'Contactless card & NFC payment register', 499.99, 'USD', 25, 'active'),
    ('p0000000-0000-4000-b000-000000000002', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'SKU-GLOB-2002', 'Thermal Receipt Paper Roll 50-pack', 'BPA-free high density paper rolls', 29.99, 'USD', 100, 'active')
ON CONFLICT (product_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 4. ORDERS
-- Includes cases: delivered (normal), late, pending, returned/refunded, cancelled
-- -----------------------------------------------------------------------------
INSERT INTO orders (order_id, tenant_id, customer_id, order_number, order_status, total_amount, currency, shipping_address_masked, ordered_at, promised_delivery_at)
VALUES
    ('d0000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0000000-0000-4000-a000-000000000001', 'ORD-2026-1001', 'delivered', 345.00, 'USD', '100 Synthetic Way, Suite ***, Austin TX', NOW() - INTERVAL '10 days', NOW() - INTERVAL '3 days'),
    ('d0000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0000000-0000-4000-a000-000000000002', 'ORD-2026-1002', 'late', 1200.00, 'USD', '250 Example Tech Blvd, Bldg ***, San Jose CA', NOW() - INTERVAL '5 days', NOW() - INTERVAL '1 day'),
    ('d0000000-0000-4000-a000-000000000003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0000000-0000-4000-a000-000000000003', 'ORD-2026-1003', 'pending', 150.00, 'USD', '789 Fictional Ave, Floor ***, Seattle WA', NOW() - INTERVAL '1 day', NOW() + INTERVAL '3 days'),
    ('d0000000-0000-4000-b000-000000000004', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0000000-0000-4000-b000-000000000004', 'ORD-2026-2001', 'returned', 499.99, 'USD', '555 Gotham Center, Tower ***, New York NY', NOW() - INTERVAL '12 days', NOW() - INTERVAL '8 days'),
    ('d0000000-0000-4000-b000-000000000005', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0000000-0000-4000-b000-000000000005', 'ORD-2026-2002', 'cancelled', 29.99, 'USD', '404 Skynet Plaza, Suite ***, Los Angeles CA', NOW() - INTERVAL '2 days', NOW() + INTERVAL '2 days')
ON CONFLICT (order_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 5. ORDER_ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_item_id, tenant_id, order_id, product_id, quantity, unit_price, subtotal)
VALUES
    ('i0000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000001', 'p0000000-0000-4000-a000-000000000001', 2, 150.00, 300.00),
    ('i0000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000001', 'p0000000-0000-4000-a000-000000000003', 1, 45.00, 45.00),
    ('i0000000-0000-4000-a000-000000000003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000002', 'p0000000-0000-4000-a000-000000000002', 1, 1200.00, 1200.00),
    ('i0000000-0000-4000-a000-000000000004', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000003', 'p0000000-0000-4000-a000-000000000001', 1, 150.00, 150.00),
    ('i0000000-0000-4000-b000-000000000005', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0000000-0000-4000-b000-000000000004', 'p0000000-0000-4000-b000-000000000001', 1, 499.99, 499.99),
    ('i0000000-0000-4000-b000-000000000006', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0000000-0000-4000-b000-000000000005', 'p0000000-0000-4000-b000-000000000002', 1, 29.99, 29.99)
ON CONFLICT (order_item_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 6. PAYMENTS
-- Includes completed, pending, refunded, and failed payment cases
-- -----------------------------------------------------------------------------
INSERT INTO payments (payment_id, tenant_id, order_id, payment_reference, payment_method, payment_status, amount, currency, processed_at)
VALUES
    ('e0000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000001', 'PAY-SYNTH-1001', 'purchase_order', 'completed', 345.00, 'USD', NOW() - INTERVAL '10 days'),
    ('e0000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000002', 'PAY-SYNTH-1002', 'bank_transfer', 'completed', 1200.00, 'USD', NOW() - INTERVAL '5 days'),
    ('e0000000-0000-4000-a000-000000000003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0000000-0000-4000-a000-000000000003', 'PAY-SYNTH-1003', 'credit_card', 'pending', 150.00, 'USD', NULL),
    ('e0000000-0000-4000-b000-000000000004', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0000000-0000-4000-b000-000000000004', 'PAY-SYNTH-2001', 'credit_card', 'refunded', 499.99, 'USD', NOW() - INTERVAL '11 days'),
    ('e0000000-0000-4000-b000-000000000005', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'd0000000-0000-4000-b000-000000000005', 'PAY-SYNTH-2002', 'credit_card', 'failed', 29.99, 'USD', NOW() - INTERVAL '2 days')
ON CONFLICT (payment_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 7. SUPPORT_TICKETS
-- Includes cases: open/urgent, closed/normal, pending, rejected
-- -----------------------------------------------------------------------------
INSERT INTO support_tickets (support_ticket_id, tenant_id, customer_id, order_id, ticket_number, subject, priority, status, category)
VALUES
    ('f0000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0000000-0000-4000-a000-000000000002', 'd0000000-0000-4000-a000-000000000002', 'TCK-ACME-1001', 'Urgent: Router shipment ORD-2026-1002 is late', 'urgent', 'open', 'order_status'),
    ('f0000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0000000-0000-4000-a000-000000000001', 'd0000000-0000-4000-a000-000000000001', 'TCK-ACME-1002', 'Copy of commercial invoice requested', 'normal', 'closed', 'billing'),
    ('f0000000-0000-4000-b000-000000000003', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0000000-0000-4000-b000-000000000004', 'd0000000-0000-4000-b000-000000000004', 'TCK-GLOB-2001', 'Return & Refund request for POS Terminal', 'high', 'pending', 'refund_request'),
    ('f0000000-0000-4000-b000-000000000004', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'c0000000-0000-4000-b000-000000000005', 'd0000000-0000-4000-b000-000000000005', 'TCK-GLOB-2002', 'Invalid compensation claim on cancelled order', 'low', 'rejected', 'refund_request')
ON CONFLICT (support_ticket_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 8. TICKET_EVENTS
-- Chronological event chain for support inquiries
-- -----------------------------------------------------------------------------
INSERT INTO ticket_events (ticket_event_id, tenant_id, support_ticket_id, actor_type, actor_id, event_type, message_body)
VALUES
    ('e0000001-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'f0000000-0000-4000-a000-000000000001', 'customer', 'c0000000-0000-4000-a000-000000000002', 'created', 'Our router order was expected yesterday. We need tracking updates immediately.'),
    ('e0000001-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'f0000000-0000-4000-a000-000000000001', 'ai_agent', 'agent_order_resolution_v1', 'comment_added', 'Verified status with carrier: Shipment delayed due to weather in transit hub. Estimated delivery updated to tomorrow.'),
    ('e0000001-0000-4000-b000-000000000003', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'f0000000-0000-4000-b000-000000000003', 'customer', 'c0000000-0000-4000-b000-000000000004', 'created', 'Item returned to warehouse. Requesting $499.99 credit back to payment card.'),
    ('e0000001-0000-4000-b000-000000000004', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'f0000000-0000-4000-b000-000000000003', 'ai_agent', 'agent_refund_v1', 'status_changed', 'Refund request generated and placed in HITL approval queue per policy rules.')
ON CONFLICT (ticket_event_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 9. APPROVAL_REQUESTS
-- Includes pending (HITL gate), approved, and rejected cases
-- -----------------------------------------------------------------------------
INSERT INTO approval_requests (approval_request_id, tenant_id, support_ticket_id, order_id, request_type, requested_by_agent, approver_id, status, proposed_action_payload, reason, decided_at)
VALUES
    ('10000000-0000-4000-b000-000000000001', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'f0000000-0000-4000-b000-000000000003', 'd0000000-0000-4000-b000-000000000004', 'refund_processing', 'agent_refund_v1', NULL, 'pending', '{"refund_amount": 499.99, "currency": "USD", "refund_method": "credit_card", "order_number": "ORD-2026-2001"}'::jsonb, 'Customer returned merchandise; awaiting human manager sign-off.', NULL),
    ('10000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'f0000000-0000-4000-a000-000000000002', 'd0000000-0000-4000-a000-000000000001', 'address_change', 'agent_profile_v1', 'op_user_42', 'approved', '{"old_address": "Original St", "new_address": "100 Synthetic Way, Suite ***, Austin TX"}'::jsonb, 'Customer address update verified by operator.', NOW() - INTERVAL '9 days'),
    ('10000000-0000-4000-b000-000000000003', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'f0000000-0000-4000-b000-000000000004', 'd0000000-0000-4000-b000-000000000005', 'refund_processing', 'agent_refund_v1', 'mgr_user_07', 'rejected', '{"refund_amount": 29.99, "reason": "Compensation claim"}'::jsonb, 'Rejected: Payment failed prior to shipping; no funds captured.', NOW() - INTERVAL '1 day')
ON CONFLICT (approval_request_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 10. AGENT_ACTION_AUDIT
-- Tracks agent tool executions, HITL blockages, completions, and failures
-- -----------------------------------------------------------------------------
INSERT INTO agent_action_audit (agent_action_audit_id, tenant_id, agent_id, agent_role, action_name, target_entity_type, target_entity_id, execution_status, input_parameters, output_result, error_message)
VALUES
    ('20000000-0000-4000-a000-000000000001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'supervisor_agent', 'supervisor', 'route_inquiry', 'support_tickets', 'f0000000-0000-4000-a000-000000000001', 'completed', '{"ticket_id": "f0000000-0000-4000-a000-000000000001"}'::jsonb, '{"target_agent": "order_resolution_agent"}'::jsonb, NULL),
    ('20000000-0000-4000-a000-000000000002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'agent_order_resolution_v1', 'order_resolution', 'verify_order_status', 'orders', 'd0000000-0000-4000-a000-000000000002', 'completed', '{"order_number": "ORD-2026-1002"}'::jsonb, '{"status": "late", "promised_delivery_at": "2026-07-28T00:00:00Z"}'::jsonb, NULL),
    ('20000000-0000-4000-b000-000000000003', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'agent_refund_v1', 'refund_processor', 'request_refund_approval', 'approval_requests', '10000000-0000-4000-b000-000000000001', 'blocked_hitl', '{"order_id": "d0000000-0000-4000-b000-000000000004", "amount": 499.99}'::jsonb, '{"approval_request_id": "10000000-0000-4000-b000-000000000001", "status": "pending_human_review"}'::jsonb, NULL),
    ('20000000-0000-4000-b000-000000000004', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'agent_refund_v1', 'refund_processor', 'direct_refund_execute', 'orders', 'd0000000-0000-4000-b000-000000000005', 'failed', '{"order_id": "d0000000-0000-4000-b000-000000000005"}'::jsonb, NULL, 'Blocked by Policy Guardrail: Mandatory HITL approval required for financial refunds.')
ON CONFLICT (agent_action_audit_id) DO NOTHING;

COMMIT;
