-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 28, 2024 at 11:13 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `thesis_base`
--

-- --------------------------------------------------------

--
-- Table structure for table `advisor`
--

CREATE TABLE `advisor` (
  `advisor_id` int(11) NOT NULL,
  `advisor_name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `advisor`
--

INSERT INTO `advisor` (`advisor_id`, `advisor_name`) VALUES
(1, 'ผศ.อัจฉรา นามบุรี'),
(4, 'อ.ดร.บวรรัตน์ ศรีมาน'),
(6, 'อ.ดร.ศศิธร สุชัยยะ'),
(7, 'ผศ.วไลลักษณ์ วงษ์รื่น'),
(12, 'ผศ.ดร.จักรนรินทร์ คงเจริญ'),
(13, 'ผศ.ดร.สุรศักดิ์ ตั้งสกุล'),
(14, 'ผศ.จิตสราญ สีกู่กา'),
(15, 'ผศ.ดร.จารุวัฒน์ ไพใหล'),
(18, 'ผศ.ศิริพร ทับทิม'),
(19, 'ผศ.ดร.ถนอมศักดิ์ วงศ์มีแก้ว'),
(20, 'อ.ดร.สาวิณี แสงสุริยันต์'),
(21, 'ผศ.ฐาปนี เฮงสนั่นกูล'),
(22, 'ผศ.ดร.สุภาพ กัญญาคำ'),
(23, 'รศ.ดร.พีระ ลิ่วลม');

-- --------------------------------------------------------

--
-- Table structure for table `file_documents`
--

CREATE TABLE `file_documents` (
  `file_id` int(11) NOT NULL,
  `doc_id` int(11) DEFAULT NULL,
  `file_name` varchar(100) DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reset_password_tokens`
--

CREATE TABLE `reset_password_tokens` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `expired_status` tinyint(1) DEFAULT 0,
  `expire_date` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `term`
--

CREATE TABLE `term` (
  `term_id` int(11) NOT NULL,
  `term` varchar(255) NOT NULL,
  `frequency` int(11) NOT NULL,
  `doc_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `thesis_document`
--

CREATE TABLE `thesis_document` (
  `doc_id` int(11) NOT NULL,
  `title_th` varchar(255) NOT NULL,
  `title_en` varchar(255) NOT NULL,
  `user_id` int(11) NOT NULL,
  `advisor_id` int(11) NOT NULL,
  `year` int(11) NOT NULL,
  `abstract` text NOT NULL,
  `recheck_status` tinyint(1) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user_accounts`
--

CREATE TABLE `user_accounts` (
  `user_id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `firstname` varchar(255) NOT NULL,
  `lastname` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `access_role` tinyint(1) NOT NULL DEFAULT 0 COMMENT ' 0 - nisit 1- admin',
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `deleted_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `advisor`
--
ALTER TABLE `advisor`
  ADD PRIMARY KEY (`advisor_id`);

--
-- Indexes for table `file_documents`
--
ALTER TABLE `file_documents`
  ADD PRIMARY KEY (`file_id`),
  ADD KEY `doc_id_fk` (`doc_id`);

--
-- Indexes for table `reset_password_tokens`
--
ALTER TABLE `reset_password_tokens`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `token` (`token`),
  ADD KEY `resetpwd_userid_fk` (`user_id`);

--
-- Indexes for table `term`
--
ALTER TABLE `term`
  ADD PRIMARY KEY (`term_id`),
  ADD KEY `term_doc_id_fk` (`doc_id`);

--
-- Indexes for table `thesis_document`
--
ALTER TABLE `thesis_document`
  ADD PRIMARY KEY (`doc_id`),
  ADD KEY `advisor_id_fk` (`advisor_id`),
  ADD KEY `user_id_fk` (`user_id`);

--
-- Indexes for table `user_accounts`
--
ALTER TABLE `user_accounts`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `advisor`
--
ALTER TABLE `advisor`
  MODIFY `advisor_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `file_documents`
--
ALTER TABLE `file_documents`
  MODIFY `file_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `reset_password_tokens`
--
ALTER TABLE `reset_password_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `term`
--
ALTER TABLE `term`
  MODIFY `term_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `thesis_document`
--
ALTER TABLE `thesis_document`
  MODIFY `doc_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_accounts`
--
ALTER TABLE `user_accounts`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `file_documents`
--
ALTER TABLE `file_documents`
  ADD CONSTRAINT `doc_id_fk` FOREIGN KEY (`doc_id`) REFERENCES `thesis_document` (`doc_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `reset_password_tokens`
--
ALTER TABLE `reset_password_tokens`
  ADD CONSTRAINT `resetpwd_userid_fk` FOREIGN KEY (`user_id`) REFERENCES `user_accounts` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `term`
--
ALTER TABLE `term`
  ADD CONSTRAINT `term_doc_id_fk` FOREIGN KEY (`doc_id`) REFERENCES `thesis_document` (`doc_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `thesis_document`
--
ALTER TABLE `thesis_document`
  ADD CONSTRAINT `advisor_id_fk` FOREIGN KEY (`advisor_id`) REFERENCES `advisor` (`advisor_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `user_accounts` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
