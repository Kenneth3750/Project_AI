drop database if exists prueba_ai;
create database if not exists prueba_ai;

use prueba_ai;

create table if not exists users (
    id int primary key auto_increment,
    user_email varchar(100) not null unique,
    user_full_name varchar(200) not null,
    user_name varchar(50) not null,
    photo_url varchar(400) not null
);


create table if not exists roles (
    id int primary key auto_increment,
    role_name varchar(50) not null
);

create table if not exists user_conversations (
    id int primary key auto_increment,
    user_id int not null,
    role_id int not null,
    conversations json not null,
    created_at date not null,
    foreign key (user_id) references users(id) on delete cascade,
    foreign key (role_id) references roles(id) on delete cascade
);

create table if not exists user_conversation_history (
    id int primary key auto_increment,
    user_id int not null,
    role_id int not null,
    user_resume text not null,
    created_at date not null,
    foreign key (user_id) references users(id) on delete cascade,
    foreign key (role_id) references roles(id) on delete cascade
);


create table if not exists recepcionist_reservations (
    id int primary key auto_increment,
    user_id int not null,
    place varchar(50) not null,
    reservation_date date not null,
    reservation_start_time time not null,
    reservation_end_time time not null,
    user_name varchar(50) not null,
    created_at date not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists assistant_emails_registerd (
    id int primary key auto_increment,
    user_id int not null,
    email_json json not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists recepcionist_apartments (
    id int primary key auto_increment,
    user_id int not null,
    apartment_json json not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists recepcionist_areas (
    id int primary key auto_increment,
    user_id int not null,
    areas_array json not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists trainer_summaries (
    id int primary key auto_increment,
    user_id int not null,
    summary_html text not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists investigator_long_texts (
    id int primary key auto_increment,
    user_id int not null,
    long_text text not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists user_useful_info(
    id int primary key auto_increment,
    user_id int not null,
    city varchar(100) not null,
    country varchar(100) not null,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists university_emails(
    id int primary key auto_increment,
    user_id int not null,
    email varchar(100) not null,
    foreign key (user_id) references users(id) on delete cascade
);





insert into roles (role_name) values ('Investigator');
insert into roles (role_name) values ('Hotel');
insert into roles (role_name) values ('Trainer');
insert into roles (role_name) values ('PersonalAssistant');
insert into roles (role_name) values ('Tutor');
