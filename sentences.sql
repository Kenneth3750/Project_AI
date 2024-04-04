drop database if exists prueba_ai;
create database if not exists prueba_ai;

use prueba_ai;

create table if not exists users (
    id int primary key auto_increment,
    user_name varchar(50) not null
);

create table if not exists user_conversations (
    id int primary key auto_increment,
    user_id int not null,
    conversations json not null,
    created_at timestamp default current_timestamp,
    foreign key (user_id) references users(id) on delete cascade
);

create table if not exists user_conversation_history (
    id int primary key auto_increment,
    user_id int not null,
    user_resume text not null,
    foreign key (user_id) references users(id) on delete cascade
);



insert into users (user_name) values ('Kenneth');