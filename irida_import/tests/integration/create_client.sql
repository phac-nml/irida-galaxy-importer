-- remote apis
INSERT INTO client_details (id,clientId,clientSecret,token_validity,refresh_validity,createdDate,modifiedDate) VALUES (1,"myClient","myClientSecret",100000,2592000,now(),now());
INSERT INTO client_details_grant_types (client_details_id,grant_value) VALUES (1,"password");
INSERT INTO client_details_scope (client_details_id,scope) VALUES (1,"read");
INSERT INTO client_details_scope (client_details_id,scope) VALUES (1,"write");
-- galaxy auth connection
INSERT INTO client_details (id,clientId,clientSecret,token_validity,refresh_validity,createdDate,modifiedDate,redirect_uri) VALUES (2,"auth_code_client","auth_code_secret",100000,2592000,now(),now(),"http://127.0.0.1:8080/galaxy/auth_code");
INSERT INTO client_details_grant_types (client_details_id,grant_value) VALUES (2,"authorization_code");
INSERT INTO client_details_scope (client_details_id,scope) VALUES (2,"read");

-- user -- password encryption of `password1`
INSERT INTO user (`createdDate`, `modifiedDate`, `email`, `firstName`, `lastName`, `locale`, `password`, `phoneNumber`, `username`, `enabled`, `system_role`, `credentialsNonExpired`) VALUES (now(), now() , 'jeffrey.thiessen@phac-aspc.gc.ca', 'Jeffrey', 'Thiessen', 'en', '$2a$10$yvzFLxWA9m2wNQmHpJtWT.MRZv8qV8Mo3EMB6HTkDnUbi9aBrbWWW', '0000', 'jeff', 1, 'ROLE_ADMIN', 1);
