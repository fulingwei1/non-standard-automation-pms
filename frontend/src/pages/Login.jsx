import React, { useState } from 'react';
import { authApi } from '../services/api';
import { Box, Lock, User, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

const Login = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await authApi.login(formData);
            localStorage.setItem('token', response.data.access_token);
            onLoginSuccess();
        } catch (err) {
            setError(err.response?.data?.detail || '登录失败，请检查用户名和密码');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            height: '100vh',
            width: '100vw',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'radial-gradient(circle at top right, #1e1b4b, #050505)',
            position: 'fixed',
            top: 0,
            left: 0,
            zIndex: 1000
        }}>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel"
                style={{
                    width: '400px',
                    padding: '40px',
                    textAlign: 'center',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                }}
            >
                <div style={{
                    width: '64px',
                    height: '64px',
                    background: 'var(--primary-color)',
                    borderRadius: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                    boxShadow: '0 0 20px var(--primary-glow)'
                }}>
                    <Box color="white" size={32} />
                </div>

                <h1 style={{ marginBottom: '8px', fontSize: '1.8rem' }}>欢迎回来</h1>
                <p style={{ color: 'var(--text-dim)', marginBottom: '32px' }}>请输入您的凭据以访问系统</p>

                <form onSubmit={handleSubmit} style={{ textAlign: 'left' }}>
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '8px', marginLeft: '4px' }}>用户名</label>
                        <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <User size={18} color="var(--text-dim)" />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="您的用户名"
                                required
                                style={{ background: 'none', border: 'none', outline: 'none', color: 'white', width: '100%' }}
                            />
                        </div>
                    </div>

                    <div style={{ marginBottom: '32px' }}>
                        <label style={{ display: 'block', color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '8px', marginLeft: '4px' }}>密码</label>
                        <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Lock size={18} color="var(--text-dim)" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                style={{ background: 'none', border: 'none', outline: 'none', color: 'white', width: '100%' }}
                            />
                        </div>
                    </div>

                    {error && <p style={{ color: '#f43f5e', fontSize: '0.85rem', marginBottom: '16px', textAlign: 'center' }}>{error}</p>}

                    <button
                        className="btn-primary"
                        disabled={loading}
                        style={{
                            width: '100%',
                            padding: '14px',
                            fontSize: '1rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px'
                        }}
                    >
                        {loading ? '认证中...' : '立即登录'} <ArrowRight size={18} />
                    </button>
                </form>
            </motion.div>
        </div>
    );
};

export default Login;
