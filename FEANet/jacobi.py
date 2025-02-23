import torch
import numpy as np
import torch.nn.functional as F

class JacobiBlock():
    """ Define all the methods necessary for a CNN-based Jacobi iteration (Dirichlet boundary condition)
        
        Knet: neural network model for stiffness terms
        mesh: an object that define the mesh
        initial_u : tensor-like, shape = [*, *, n, n]
            Initial values of the variable.
        geometry_idx : tensor-like, shape = [*, *, n, n]
            Matrix describing the domain: 1.0 for inner points 0.0 elsewhere.
        boundary_value: tensor-like, shape = [*, *, n, n]
            Matrix describing the domain: desired values for boundary points 0.0 elsewhere.
    """
    def __init__(self, Knet, mesh, omega, geometry_idx, boundary_value):
        self.nnode_edge = geometry_idx.shape[2]
        self.geometry_idx = geometry_idx
        self.boundary_value = boundary_value
        self.omega = omega
        self.mesh = mesh
        self.d_mat = torch.zeros_like(geometry_idx) # Diagonal matrix for Jacobi iteration
        self.compute_diagonal_matrix()
        self.Knet = Knet # Initialize the stiffness network, given mesh

    def reset_boundary(self, u):
        """ Reset values at the boundary of the domain """
        return u * self.geometry_idx + self.boundary_value

    def compute_diagonal_matrix(self):
        """ Comopute diagonal matrix for Jacobi iteration """
        for i in range(self.d_mat.shape[0]):
            for pkey in self.mesh.kernel_dict:
                K_weights = torch.from_numpy(self.mesh.kernel_dict[pkey]) ## 3x3 size kernel
                global_pattern = torch.from_numpy(self.mesh.global_pattern_center[pkey]).reshape(self.nnode_edge, self.nnode_edge)
                self.d_mat[i,0,:,:] += global_pattern*K_weights[1,1] 

    def jacobi_convolution(self, initial_u, forcing_term):
        """ Jacobi method iteration step defined as a convolution:
        u_new = omega/d_mat*residual + u, where residual = f - K*u (* is convolution operator here)
        note that the forcing_term should be already convoluted, i.e., forcing_term = fnet(f), when source term is f
        """
        u = self.reset_boundary(initial_u)
        residual = forcing_term-self.Knet(u)
        u_new = self.omega/self.d_mat*residual + u
        return self.reset_boundary(u_new)


class JacobiBlockPBC():
    """ Define all the methods necessary for a CNN-based Jacobi iteration (periodic boundary condition); currently only for homogeneous problems
        
        Knet: neural network model for stiffness terms
    """
    def __init__(self, mesh, Knet=None, omega=2./3.):
        self.nnode_edge = mesh.nnode_edge 
        self.omega = omega
        self.mesh = mesh
        self.d_mat = torch.zeros((1,1,self.nnode_edge, self.nnode_edge)) # Diagonal matrix for Jacobi iteration
        self.compute_diagonal_matrix()
        self.Knet = Knet # Initialize the stiffness network, given mesh

    def compute_diagonal_matrix(self):
        """ Comopute diagonal matrix for Jacobi iteration """
        for i in range(self.d_mat.shape[0]):
            for pkey in self.mesh.kernel_dict:
                K_weights = torch.from_numpy(self.mesh.kernel_dict[pkey]) ## 3x3 size kernel
                global_pattern = torch.from_numpy(self.mesh.global_pattern_center[pkey]).reshape(self.nnode_edge, self.nnode_edge)
                self.d_mat[i,0,:,:] += global_pattern*K_weights[1,1] 

    def pbc_boundary(self, u):
        """ 
        Expand the domain boundary to be periodic
        Input size [n+1, n+1]; output size [n+3, n+3]
        """
        u_central = u[:,:,:-1,:-1].clone()
        return F.pad(u_central, (1,2,1,2), 'circular')

    def reset_boundary(self, u):
        """ 
        Copy the boundary values to be the same
        Input size [n+1, n+1]; output size [n+1, n+1]
        """
        u_central = u[:,:,:-1,:-1].clone()
        return F.pad(u_central, (0,1,0,1), 'circular')

    def jacobi_convolution(self, u, forcing_term):
        """ 
        Jacobi method iteration step defined as a convolution:
        u_new = omega/d_mat*residual + u, where residual = f - K*u (* is convolution operator here)
        note that the forcing_term should be already convoluted, i.e., forcing_term = fnet(f), when source term is f
        """
        u_pbc = self.pbc_boundary(u)
        residual = forcing_term-self.Knet(u_pbc)
        residual = residual[:,:,1:-1,1:-1].clone() # due to padding = 1, need to remove the most outside boundary layer of residual
        u_new = self.omega/self.d_mat*residual + self.reset_boundary(u)
        return u_new